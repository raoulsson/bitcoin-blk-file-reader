# bitcoin-blk-file-reader
Reads the blkXXXXX.dat files from bitcoind (Bitcoin-Core)
The implementation is in python and includes the witness format for the extended transaction format and includes correct transaction hash calculation, which was initially forgotten to add here.

## Usage
Normally your bitcoind client stores the blk files in $HOME/.bitcoin/blocks/

To read the first blk-file, which is blk00000.dat:

```shell
python analyze.py $HOME/.bitcoin/blocks/blk00000.dat
```

After that you get the output to the console. This script is very easy to understand and you can use it on your own.

NOTICE: Some addresses are not calculated yet, they are multisig addresses, I did not have time to add the code, but I will. Further the code is not very nice, since this was my first try doing this long ago. But feel free to contact me if you have any questions.

# Update: July 2022 - raoulsson
Adapted code to run under Python 3.x. Added two params to log only one block, by number script parameter, or a block and a transaction by number. Again by param. Like:

Usage: python analyze.py <file-path> <block-to-log> <transaction-of-that-block-to-log>

Note: publicKeyDecode() for address currently not working. Will fix soon.

(I neeed this to check my Java bitcoin "core" playground implementation. Actually the compact varInt in file blk000976.dat gave me a headache...)



