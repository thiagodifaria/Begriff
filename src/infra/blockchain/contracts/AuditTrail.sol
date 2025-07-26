// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract AuditTrail {
    mapping(bytes32 => uint256) public auditRecords;
    event RecordAdded(bytes32 indexed recordHash, uint256 timestamp);

    function addRecord(bytes32 _recordHash) public {
        require(auditRecords[_recordHash] == 0, "Record already exists.");
        auditRecords[_recordHash] = block.timestamp;
        emit RecordAdded(_recordHash, block.timestamp);
    }
}
