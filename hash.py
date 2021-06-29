#!/usr/bin/python3
import hashLib, colorama

if __name__ == '__main__':
    print('hash.py: Hash a password for PHFS config.\n')
    print('Input password: %s%s' % (colorama.Back.WHITE, colorama.Fore.WHITE), end='')
    password = input()
    print('%s%s' % (colorama.Back.RESET, colorama.Fore.RESET), end='')
    hashed = hashLib.PasswordToBaseHash(password).get()
    print('Result: %s%s%s' % (colorama.Back.WHITE, hashed, colorama.Fore.WHITE), end='')
    print('%s%s' % (colorama.Back.RESET, colorama.Fore.RESET))
