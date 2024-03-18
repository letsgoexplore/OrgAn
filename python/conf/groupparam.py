from charm.toolbox.ecgroup import ECGroup, ZR, G
from charm.toolbox.eccurve import secp112r1, secp128r1, secp160k1, prime192v1, secp256k1, sect283k1, secp384r1, \
    sect571r1
from decimal import *

group112 = ECGroup(secp112r1)
group128 = ECGroup(secp128r1)
group160 = ECGroup(secp160k1)
group192 = ECGroup(prime192v1)
group256 = ECGroup(secp256k1)
group283 = ECGroup(sect283k1)
group384 = ECGroup(secp384r1)
group571 = ECGroup(sect571r1)

decoded_g160 = b'\x00L}\xf8_\xf8\xf9\x14\x86\xa2\xfe_\x93SA\xa6\xab'
decoded_h160 = b'\x00N\xcc\xd9\x1c\x83\xd5\x843x\xc1,\xabs\xc1,\xbc'
decoded_g192 = b'\xab\xd0}\x86\xe1\x92,\xdd Ceael\x1a\xc3\xb9\xf5a\xe9K\xcd7\xa4'
decoded_h192 = b'\x00\xa3\x0brz\xea\xb0\xba\x005\t\xf9\xe9\xd2\x84\x0b\x18\x02\x18\xc2\xd7E\x13D'
decoded_g256 = b'\xba\x98\x0e\x99\xe1fF\xa5\x08\xc4\x1f%\xae\rz\x85\x83\x14\xc9(\x9e,\x18[,\xc9\x9f\xae'
decoded_h256 = b'\xb6?[\xe9\xa4&\x02\x84\xf2^\x9e\xe8<\xd52\x11\x8fg\x16.\xa2:o\xd3\xa7\x9e\x14e'
decoded_g283 = b'\x03\xea\xc1\x12\xfd\x03U\xcf\xe7\xdd\xd1\xbe\xb9"\xd0\xeec\xff\xb4~u;\xbb(\xaa?\xb8\xfb\x16\x98|\x8c'
decoded_h283 = b'\x00\xf5+\xe2H*\x13\xa1\xbbW\x91\xd7P\xb4\xf5\xfa\x81\xfb\x12W\x1f\xa1\xaeP8\xb1\x0fE\xc4\xa7F\n'
decoded_g384 = b'p"C\x9e\x03\xa6\xfcuF\x12\x12\xca\xc8*\x81\xb9\x89\x0fn\xdb\x8f\xff\xca\xd5\xcbY|\xd2\xe0\tX\xa0\xf5\xf8\x9b\x0e\x9e\x82\xd7\x0c\x8a\xe5c8'
decoded_h384 = b'\xb6y\x98\xf5\xee\xc0\xd7\xe3x\xa6\x00\xf1\xee\x05\xad\x08%\xa7\x90{N\xc6\xdfO\xc9~\x88U;\xfa0\xa4\xb7\xcd\xc7\x0e\xf6m\x91oFE\xb7z'
decoded_g571 = b'\x00F;V\xc9\x86\xfd-I\xe2\xc9z\xa1\x0c)\x8f\x1c94}\xbc\xd8g\xcc\xda\x13\xac1\xb2\x870?\xa2\xa3\xb2r\x14\x8b\xc3\xbb\x99y$x5V\xee\xf4\xa0\xaa\x87d\xce\xae\xd1\xf3 \xce8\xf2*\x1e\xf9\xc4o\x0f\xf8\xa2'
decoded_h571 = b'\x07g\x93\x0c\xde\xb3\xb8\x1a\xcf\xa8+\n\xf9W&m\xd2q\x97\x17\xd6\xa1W\xa0\xe6\xae\x1a_Z\x02_\xcc\x9f\x97\xc1\x81\x01\x96\\<E\x05f\xe3\xd3S.\x04P\xd6\xad}\x82\xc00\x1b\xc2\xbb\xb5*\xa4~\x91c\x80+\xbex'

# Assign to 'group' the default group of choice

bits = 32
group_zv = group384

if bits == 256:
    group_zq = group283
    group_zp = group256
    share_vector_length = 8192
    p = group_zp.order()
    ring_v = (262 * (2 ** 360)) + 1

if bits == 226:
    # noutput = s
    group_zq = group256
    share_vector_length = 8192
    p = 2 ** 226 - 5
    ring_v = (7 * (2 ** 290)) + 1

elif bits == 128:
    group_zq = group160
    group_zp = group128
    share_vector_length = 4096
    p = group_zp.order()
    ring_v = (102 * (2 ** 256)) + 1

elif bits == 64:
    group_zq = group112
    p = 2 ** 64 - 59
    share_vector_length = 2048
    ring_v = (102 * (2 ** 256)) + 1

elif bits == 32:
    group_zq = group112
    p = 2 ** 32 - 5
    share_vector_length = 2048
    ring_v = (57 * (2 ** 96)) + 1

v = group_zv.order()
q = group_zq.order()

if bits == 32:
    # q = 2 ** 56 - 5
    q = group112.order()

getcontext().prec = 571
pqratio = Decimal(int(p)) / Decimal(int(q))
qvratio = Decimal(int(q)) / Decimal(int(ring_v))

bulk_qvratio = Decimal(int(group256.order())) / Decimal(int((7 * (2 ** 290)) + 1))

base_p = 2 ** 32 - 5
#base_q = 2 ** 56 - 5
base_q = group112.order()
base_ring_v = (57 * (2 ** 96)) + 1
base_share_vector_length = 2048

group_zp = group256
bulk_p = 2 ** 226 - 5
bulk_q = group256.order()
bulk_ring_v = (7 * (2 ** 290)) + 1
bulk_share_vector_length = 8192

# QBASE = 2 ** 56 - 5
QBASE = group112.order()
PBULK = 2 ** 226 - 5
QBULK = int(group256.order())

BASE_PARAMS = {
    'P': 2 ** 32 - 5,
    #'Q': 2 ** 56 - 5,
    'Q': int(group112.order()),

    'RING_V': (57 * (2 ** 96)) + 1,
    'VECTOR_LENGTH': 2048,
    'BITS': 32
}

BULK_PARAMS = {
    'P': PBULK,
    'Q': QBULK,
    'RING_V': (7 * (2 ** 290)) + 1,
    'VECTOR_LENGTH': 8192,
    'BITS': 226
}

NODE_PARAMS = {
    'N_NODES': 2,
    'N_CLIENTS': 2,
    'N_SUPER_CLIENTS': 1,
    'N_SLOTS': 2,
    'N_SUB_CLIENTS': 1,
    'START_CLIENT_INDEX': 0,
    'END_CLIENT_INDEX': 0
}

SLOT_PARAMS = {
    'FRAGMENTS': 1,
    'SLOT_NUMBER': 1
}
