import binascii
import struct
import datetime
import hashlib
import base58
import sys
import traceback
import os

logBlockNum = -1
logTxNum = -1

blockCount = 0


def log(string):
    print(string)
    pass


def startsWithOpNCode(pub):
    try:
        intValue = int(pub[0:2], 16)
        if 1 <= intValue <= 75:
            return True
    except:
        pass
    return False


def publicKeyDecode(pub):
    if pub.lower().startswith(b'76a914'):
        pub = pub[6:-4]
        result = b'\x00' + binascii.unhexlify(pub)
        h5 = hashlib.sha256(result)
        h6 = hashlib.sha256(h5.digest())
        result += h6.digest()[:4]
        return base58.b58encode(result)
    elif pub.lower().startswith(b'a9'):
        return ""
    elif startsWithOpNCode(pub):
        pub = pub[2:-2]
        h3 = hashlib.sha256(binascii.unhexlify(pub))
        h4 = hashlib.new('ripemd160', h3.digest())
        result = b'\x00' + h4.digest()
        h5 = hashlib.sha256(result)
        h6 = hashlib.sha256(h5.digest())
        result += h6.digest()[:4]
        return base58.b58encode(result)
    return ""


def stringLittleEndianToBigEndian(string):
    string = binascii.hexlify(string)
    n = len(string) / 2
    fmt = '%dh' % n
    return struct.pack(fmt, *reversed(struct.unpack(fmt, string)))


def readShortLittleEndian(blockFile):
    return struct.pack(">H", struct.unpack("<H", blockFile.read(2))[0])


def readLongLittleEndian(blockFile):
    return struct.pack(">Q", struct.unpack("<Q", blockFile.read(8))[0])


def readIntLittleEndian(blockFile):
    return struct.pack(">I", struct.unpack("<I", blockFile.read(4))[0])


def hexToInt(value):
    return int(binascii.hexlify(value), 16)


def hexToStr(value):
    return binascii.hexlify(value)


def readVarInt(blockFile):
    varInt = ord(blockFile.read(1))
    returnInt = 0
    if varInt < 0xfd:
        return varInt
    if varInt == 0xfd:
        returnInt = readShortLittleEndian(blockFile)
    if varInt == 0xfe:
        returnInt = readIntLittleEndian(blockFile)
    if varInt == 0xff:
        returnInt = readLongLittleEndian(blockFile)
    return int(binascii.hexlify(returnInt), 16)


def readInput(blockFile, transactionIndex):
    previousHash = binascii.hexlify(blockFile.read(32)[::-1])
    outId = binascii.hexlify(readIntLittleEndian(blockFile))
    scriptLength = readVarInt(blockFile)
    scriptSignatureRaw = hexToStr(blockFile.read(scriptLength))
    scriptSignature = scriptSignatureRaw
    seqNo = binascii.hexlify(readIntLittleEndian(blockFile))

    if transactionIndex == logTxNum - 1 and blockCount == logBlockNum:
        log("\n" + "Input")
        log("-" * 20)
        log("> Previous Hash: " + previousHash.decode('utf-8'))
        log("> Out ID: " + outId.decode('utf-8'))
        log("> Script length: " + str(scriptLength))
        log("> Script Signature (PubKey) Raw: " + scriptSignatureRaw.decode('utf-8'))
        log("> Script Signature (PubKey): " + scriptSignature.decode('utf-8'))
        log("> Seq No: " + seqNo.decode('utf-8'))


def readOutput(blockFile, transactionIndex):
    value = hexToInt(readLongLittleEndian(blockFile)) / 100000000.0
    scriptLength = readVarInt(blockFile)
    scriptSignatureRaw = hexToStr(blockFile.read(scriptLength))
    scriptSignature = scriptSignatureRaw
    address = 'n/a'
    try:
        pass
        #address = publicKeyDecode(scriptSignature) // FIXME: broke during port to 3.x
    except Exception as e:
        print(e)
    if transactionIndex == logTxNum - 1 and blockCount == logBlockNum:
        log("\n" + "Output")
        log("-" * 20)
        log("> Value: " + str(value))
        log("> Script length: " + str(scriptLength))
        log("> Script Signature (PubKey) Raw: " + scriptSignatureRaw.decode('utf-8'))
        log("> Script Signature (PubKey): " + scriptSignature.decode('utf-8'))
        log("> Address: " + address)


def readTransaction(blockFile, transactionIndex):
    extendedFormat = False
    beginByte = blockFile.tell()
    inputIds = []
    outputIds = []
    version = hexToInt(readIntLittleEndian(blockFile))
    cutStart1 = blockFile.tell()
    cutEnd1 = 0
    inputCount = readVarInt(blockFile)

    if transactionIndex == logTxNum - 1 and blockCount == logBlockNum:
        log("\n" + "Transaction Num: " + str(transactionIndex + 1) + " of Block: " + str(blockCount))
        log("-" * 100)
        log("Version: " + str(version))

    if inputCount == 0:
        extendedFormat = True
        flags = ord(blockFile.read(1))
        cutEnd1 = blockFile.tell()
        if flags != 0:
            inputCount = readVarInt(blockFile)
            if transactionIndex == logTxNum - 1 and blockCount == logBlockNum:
                log("\nInput Count: " + str(inputCount))
            for inputIndex in range(0, inputCount):
                inputIds.append(readInput(blockFile, transactionIndex))
            outputCount = readVarInt(blockFile)
            for outputIndex in range(0, outputCount):
                outputIds.append(readOutput(blockFile, transactionIndex))
    else:
        cutStart1 = 0
        cutEnd1 = 0
        if transactionIndex == logTxNum - 1 and blockCount == logBlockNum:
            log("\nInput Count: " + str(inputCount))
        for inputIndex in range(0, inputCount):
            inputIds.append(readInput(blockFile, transactionIndex))
        outputCount = readVarInt(blockFile)
        if transactionIndex == logTxNum - 1 and blockCount == logBlockNum:
            log("\nOutput Count: " + str(outputCount))
        for outputIndex in range(0, outputCount):
            outputIds.append(readOutput(blockFile, transactionIndex))

    cutStart2 = 0
    cutEnd2 = 0
    if extendedFormat:
        if flags & 1:
            cutStart2 = blockFile.tell()
            for inputIndex in range(0, inputCount):
                countOfStackItems = readVarInt(blockFile)
                for stackItemIndex in range(0, countOfStackItems):
                    stackLength = readVarInt(blockFile)
                    stackItem = blockFile.read(stackLength)[::-1]
                    if transactionIndex == logTxNum - 1 and blockCount == logBlockNum:
                        log("Witness item: " + hexToStr(stackItem).decode('utf-8'))
            cutEnd2 = blockFile.tell()

    lockTime = hexToInt(readIntLittleEndian(blockFile))
    if lockTime < 500000000:
        if transactionIndex == logTxNum - 1 and blockCount == logBlockNum:
            log("\nLock Time is Block Height: " + str(lockTime))
    else:
        if transactionIndex == logTxNum - 1 and blockCount == logBlockNum:
            log("\nLock Time is Timestamp: " + datetime.datetime.fromtimestamp(lockTime).strftime('%Y-%m-%d %H:%M:%S'))

    endByte = blockFile.tell()
    blockFile.seek(beginByte)
    lengthToRead = endByte - beginByte
    dataToHashForTransactionId = blockFile.read(lengthToRead)
    if extendedFormat and cutStart1 != 0 and cutEnd1 != 0 and cutStart2 != 0 and cutEnd2 != 0:
        dataToHashForTransactionId = dataToHashForTransactionId[:(cutStart1 - beginByte)] + dataToHashForTransactionId[
                                                                                            (cutEnd1 - beginByte):(
                                                                                                    cutStart2 - beginByte)] + dataToHashForTransactionId[
                                                                                                                              (
                                                                                                                                      cutEnd2 - beginByte):]
    elif extendedFormat:
        print(cutStart1, cutEnd1, cutStart2, cutEnd2)
        quit()
    firstHash = hashlib.sha256(dataToHashForTransactionId)
    secondHash = hashlib.sha256(firstHash.digest())
    hashLittleEndian = secondHash.hexdigest()
    hashTransaction = stringLittleEndianToBigEndian(binascii.unhexlify(hashLittleEndian))
    if transactionIndex == logTxNum - 1 and blockCount == logBlockNum:
        log("\nHash Transaction: " + hashTransaction.decode('utf-8'))
    if extendedFormat:
        pass
        # print(hashTransaction)


def readBlock(blockFile):
    magicNumber = binascii.hexlify(blockFile.read(4))
    blockSize = hexToInt(readIntLittleEndian(blockFile))
    version = hexToInt(readIntLittleEndian(blockFile))
    previousHash = binascii.hexlify(blockFile.read(32))
    merkleHash = binascii.hexlify(blockFile.read(32))
    creationTimeTimestamp = hexToInt(readIntLittleEndian(blockFile))
    creationTime = datetime.datetime.fromtimestamp(creationTimeTimestamp).strftime('%Y-%m-%d %H:%M:%S')
    bits = hexToInt(readIntLittleEndian(blockFile))
    nonce = hexToInt(readIntLittleEndian(blockFile))
    countOfTransactions = readVarInt(blockFile)
    if blockCount == logBlockNum:
        log("\n")
        log(">" * 100)
        log("Block: " + str(blockCount) + "\n")
        log("Magic Number: " + magicNumber.decode('utf-8'))
        log("Blocksize: " + str(blockSize))
        log("Version: " + str(version))
        log("Previous Hash: " + previousHash.decode('utf-8'))
        log("Merkle Hash: " + merkleHash.decode('utf-8'))
        log("Time: " + creationTime)
        log("Bits: " + str(bits))
        log("Nonce: " + str(nonce))
        log("Count of Transactions: " + str(countOfTransactions))

    for transactionIndex in range(0, countOfTransactions):
        readTransaction(blockFile, transactionIndex)
    if blockCount == logBlockNum:
        log("<" * 100)


def main():
    log("Usage: python analyze.py <file-path> <block-to-log> <transaction-of-that-block-to-log>\n")
    global logBlockNum
    global logTxNum
    blockFilename = sys.argv[1]
    if len(sys.argv) > 2:
        logBlockNum = int(sys.argv[2])
    if len(sys.argv) > 3:
        logTxNum = int(sys.argv[3])
    fileSize = os.stat(blockFilename).st_size
    sys.stdout.write("Processing Blocks...")
    with open(blockFilename, "rb") as blockFile:
        try:
            while True:
                if blockFile.tell() == fileSize:
                    break
                global blockCount
                blockCount = blockCount + 1
                if blockCount % 25 == 0:
                    sys.stdout.write(".")
                sys.stdout.flush()
                readBlock(blockFile)
        except Exception as e:
            excType, excValue, excTraceback = sys.exc_info()
            traceback.print_exception(excType, excValue, excTraceback, limit=8, file=sys.stdout)
    log("\nTotal blocks in file: " + str(blockCount))
    log("\nFile: " + blockFilename + ". Logged block: " + str(logBlockNum) + ", transaction: " + str(logTxNum))
    log("Bye!")


if __name__ == "__main__":
    main()
