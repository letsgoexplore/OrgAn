use crate::config::ProtocolParams;
use crate::ecc::{get_order, to_scalar, G, H};
use k256::{AffinePoint, ProjectivePoint};
use rayon::prelude::*;
use rug::{Complete, Integer};
use rug_fft::{bit_rev_radix_2_intt, bit_rev_radix_2_ntt};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha512};

#[derive(Serialize, Clone, Deserialize, Default, Debug)]
pub struct SetupVector {
    pub value: Vec<Integer>,
    pub value_ntt: Vec<Integer>,
    pub product_ntt: Vec<Integer>,
    pub product: Vec<Integer>,
    pub scaled: Vec<Integer>,
    pub e: Vec<Integer>,
}

#[derive(Serialize, Clone, Deserialize, Debug)]
pub struct SetupValues {
    pub share: SetupVector,
    pub blinding: SetupVector,
    pub e: Vec<AffinePoint>,
}

#[derive(Serialize, Clone, Deserialize)]
pub struct SetupRelay {
    pub values: SetupValues,
    pub qw: Vec<Vec<AffinePoint>>,
}

#[derive(Serialize, Clone, Deserialize)]
pub enum Setup {
    SetupValues(SetupValues),
    SetupRelay(SetupRelay),
}

pub fn generate_sum_shares(n: usize, modulus: &Integer, sum: &Integer) -> Vec<Integer> {
    let mut rand = rug::rand::RandState::new();
    let mut shares: Vec<Integer> =
        std::iter::repeat_with(|| Integer::from(modulus.random_below_ref(&mut rand)))
            .take(n - 1)
            .collect();
    shares.push(
        shares
            .iter()
            .fold(sum.clone(), |acc, x| (acc + modulus - x) % modulus),
    );
    shares
}

pub fn compute_hash(slot_number: usize, vec_length: usize, ring_v: &Integer) -> Vec<Integer> {
    (0..vec_length)
        .map(|i| {
            let mut hasher = Sha512::new();
            hasher.update(slot_number.to_string());
            hasher.update(i.to_string());
            Integer::from_digits(&hasher.finalize(), rug::integer::Order::Lsf) % ring_v
        })
        .collect()
}

pub fn gen_setup_vector(params: &ProtocolParams, mut shares: Vec<Integer>) -> SetupVector {
    let mut result: SetupVector = SetupVector::default();
    let mut hash_vector = compute_hash(0, params.vector_len, &params.ring_v.order);
    let root_of_unity = params.ring_v.root_of_unity(params.vector_len);
    result.value = shares.clone();
    bit_rev_radix_2_ntt(&mut shares, &params.ring_v.order, &root_of_unity);
    bit_rev_radix_2_ntt(&mut hash_vector, &params.ring_v.order, &root_of_unity);
    result.value_ntt = shares.clone();
    result.product_ntt = shares
        .into_iter()
        .zip(hash_vector)
        .map(|(a, b)| a * b)
        .collect();
    result.product = result.product_ntt.clone();
    bit_rev_radix_2_intt(&mut result.product, &params.ring_v.order, &root_of_unity);
    result.scaled = result
        .product
        .iter()
        .map(|i| Integer::from(i * &params.q) / &params.ring_v.order)
        .collect();
    result.e = result
        .product
        .iter()
        .zip(result.scaled.iter())
        .map(|(w, z)| Integer::from(w * &params.q) - z * &params.ring_v.order)
        .collect();
    result
}

pub fn gen_setup_values(params: &ProtocolParams, shares: &Vec<Integer>) -> SetupValues {
    let share = gen_setup_vector(params, shares.clone());
    let blinding = gen_setup_vector(params, shares.clone());
    SetupValues {
        e: (0..params.vector_len)
            .map(|i| (G * to_scalar(&share.e[i]) + H * to_scalar(&blinding.e[i])).to_affine())
            .collect(),
        share: share,
        blinding: blinding,
    }
}

fn compute_d(
    order: &Integer,
    _gamma: &Vec<Integer>,
    omega: &Vec<Integer>,
    product_ntt: &Vec<Integer>,
    product: &Vec<Integer>,
) -> Vec<Integer> {
    assert_eq!(product_ntt.len(), product.len());
    (0..product_ntt.len())
        .into_par_iter()
        .map(|j| {
            let val = Integer::from(
                Integer::from(product_ntt.len()).invert(order).unwrap()
                //    * &gamma[j]
                    * Integer::sum(
                        (0..product_ntt.len())
                            .into_par_iter()
                            .map(|k| Integer::from(&product_ntt[k] * &omega[j * k]))
                            .collect::<Vec<_>>()
                            .iter(),
                    )
                    .complete(),
            ) - &product[j];
            assert_eq!(Integer::from(&val % order), Integer::from(0));
            val / order
        })
        .collect()
}

pub fn gen_setup_relay(params: &ProtocolParams, client_values: &Vec<SetupValues>) -> SetupRelay {
    let gamma = params
        .ring_v
        .root_of_unity(params.vector_len * 2)
        .invert(&params.ring_v.order)
        .unwrap();
    let omega = params
        .ring_v
        .root_of_unity(params.vector_len)
        .invert(&params.ring_v.order)
        .unwrap();
    info!("Computing gamma...");
    let gamma_inverse: Vec<Integer> = std::iter::once(Integer::from(1))
        .chain((0..params.vector_len).scan(Integer::from(1), |acc, _| {
            *acc *= &gamma;
            *acc %= &params.ring_v.order;
            Some(acc.clone())
        }))
        .collect();
    debug!("gamma: {:?}", gamma_inverse);
    info!("Computing omega...");
    let omega_inverse: Vec<Integer> = std::iter::once(Integer::from(1))
        .chain(
            (0..params.vector_len * params.vector_len).scan(Integer::from(1), |acc, _| {
                *acc *= &omega;
                *acc %= &params.ring_v.order;
                Some(acc.clone())
            }),
        )
        .collect();

    let mut hash_vector = compute_hash(0, params.vector_len, &params.ring_v.order);
    let root_of_unity = params.ring_v.root_of_unity(params.vector_len);
    bit_rev_radix_2_ntt(&mut hash_vector, &params.ring_v.order, &root_of_unity);
    info!("Computing d...");
    let d: Vec<Vec<Integer>> = (0..client_values.len())
        .into_par_iter()
        .map(|i| {
            compute_d(
                &params.ring_v.order,
                &gamma_inverse,
                &omega_inverse,
                &client_values[i].share.product_ntt,
                &client_values[i].share.product,
            )
        })
        .collect();
    info!("Computing d_...");
    let d_blinding: Vec<Vec<Integer>> = (0..client_values.len())
        .into_par_iter()
        .map(|i| {
            compute_d(
                &params.ring_v.order,
                &gamma_inverse,
                &omega_inverse,
                &client_values[i].blinding.product_ntt,
                &client_values[i].blinding.product,
            )
        })
        .collect();
    info!("Computing ab...");
    let ab: Vec<Vec<AffinePoint>> = (0..client_values.len())
        .into_par_iter()
        .map(|i| {
            (0..params.vector_len)
                .into_par_iter()
                .map(|j| {
                    (G * to_scalar(&client_values[i].share.value_ntt[j])
                        + H * to_scalar(&client_values[i].blinding.value_ntt[j]))
                    .to_affine()
                })
                .collect()
        })
        .collect();
    info!("Computing qw...");
    let qw: Vec<Vec<AffinePoint>> = (0..client_values.len())
        .into_par_iter()
        .map(|i| {
            (0..params.vector_len)
                .into_par_iter()
                .map(|k| {
                    ((G * to_scalar(&(get_order() - &params.ring_v.order * &d[i][k]))
                        + H * to_scalar(&(get_order() - &params.ring_v.order * &d_blinding[i][k]))
                        + (0..params.vector_len)
                            .into_par_iter()
                            .map(|j| {
                                ab[i][j]
                                    * to_scalar(
                                        &(Integer::from(
                                            Integer::from(params.vector_len)
                                                .invert(&params.ring_v.order)
                                                .unwrap()
                                                * &hash_vector[j]
                                                * &omega_inverse[j * k],
                                        )),
                                    )
                            })
                            .sum::<ProjectivePoint>())
                        * to_scalar(&params.q))
                    .to_affine()
                })
                .collect()
        })
        .collect();
    assert_eq!(
        qw,
        (0..client_values.len())
            .into_par_iter()
            .map(|i| {
                (0..params.vector_len)
                    .into_par_iter()
                    .map(|j| {
                        ((H * to_scalar(&client_values[i].blinding.product[j])
                            + G * to_scalar(&client_values[i].share.product[j]))
                            * to_scalar(&params.q))
                        .to_affine()
                    })
                    .collect::<Vec<_>>()
            })
            .collect::<Vec<_>>(),
    );
    let values = gen_setup_values(params, &vec![Integer::from(1); params.vector_len]);
    SetupRelay {
        values: values,
        qw: qw,
    }
}
