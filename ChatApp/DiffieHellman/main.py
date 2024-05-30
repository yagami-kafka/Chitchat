from utils.DoubleDiffie import DiffieHellman
from utils.AESAlgo import AES
from binascii import hexlify
from hashlib import sha256

alice = DiffieHellman()
bob = DiffieHellman()

alice_private_key = alice.get_private_key()
print("alice private ",alice_private_key)
alice_public_key = alice.generate_public_key()
print("alice public",alice_public_key)

bob_private_key = bob.get_private_key()
print("bob private",bob_private_key)
bob_public_key = bob.generate_public_key()
print("bob public ",bob_public_key)
print('yo type',type(bob_public_key))
alice_shared_key = alice.generate_shared_key(bob_public_key)
print(sha256(str(alice_shared_key).encode()).hexdigest())
bob_shared_key = bob.generate_shared_key(alice_public_key)
print(sha256(str(bob_shared_key).encode()).hexdigest())


print("second keys generation\n")

alice_second_private_key = alice.get_second_private_key()
bob_second_private_key = bob.get_second_private_key()

bob_second_public_key = bob.generate_second_public_key(bob_shared_key)
alice_second_public_key = alice.generate_second_public_key(alice_shared_key)

bob_second_shared_key = bob.generate_second_shared_key(alice_second_public_key,bob_shared_key)
alice_second_shared_key = alice.generate_second_shared_key(bob_second_public_key,alice_shared_key)

print(bob_second_shared_key)
print(alice_second_shared_key)



if alice_second_shared_key == bob_second_shared_key:
    print(True)
else:
    print(False)


alice_shared_static = alice.generate_shared_key_static(alice_private_key,bob_public_key)
bob_shared_static = bob.generate_shared_key_static(bob_private_key,alice_public_key)

if alice_shared_static == bob_shared_static:
    print("static shared true")
else:
    print("static shared false")

alice_second_shared_key = alice.generate_second_shared_key_static(alice_second_private_key,bob_second_public_key,alice_shared_static)
bob_second_shared_key = bob.generate_second_shared_key_static(bob_second_private_key, alice_second_public_key,bob_shared_static)

assert(alice_second_shared_key==bob_second_shared_key)

print("yo final static keys")
print(alice_second_shared_key)
print(bob_second_shared_key)



# aes_obj = AES(int(alice_second_shared_key,base=16))
# my_plaintext = "this is plain text"
# encrypted_text = aes_obj.encrypt(my_plaintext)
# print("this is ",encrypted_text)

# print("this is",aes_obj.decrypt(encrypted_text))

# import unittest
# class AES_TEST(unittest.TestCase):
#     def setUp(self):
#         master_key = 0x2b7e151628aed2a6abf7158809cf4f3c
#         print("yo master key ko type",type(master_key))
#         self.AES = AES(master_key)

#     def test_encryption(self):
#         plaintext = 0x3243f6a8885a308d313198a2e0370734
#         encrypted = self.AES.encrypt(plaintext)

#         self.assertEqual(encrypted, 0x3925841d02dc09fbdc118597196a0b32)

#     def test_decryption(self):
#         ciphertext = 0x3925841d02dc09fbdc118597196a0b32
#         decrypted = self.AES.decrypt(ciphertext)

#         self.assertEqual(decrypted, 0x3243f6a8885a308d313198a2e0370734)

# if __name__ == '__main__':
#     unittest.main()
