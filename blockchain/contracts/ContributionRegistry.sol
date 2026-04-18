// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title ContributionRegistry
 * @notice Registry for tracking contributions across institutions
 * @dev Enables inter-institutional portability of academic credits
 */
contract ContributionRegistry is AccessControl, ReentrancyGuard {
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant REGISTRAR_ROLE = keccak256("REGISTRAR_ROLE");

    // Institution structure
    struct Institution {
        string name;
        string code;
        address adminAddress;
        address ledgerContract;
        bool isActive;
        uint256 registrationTime;
    }

    // Cross-institution transfer request
    struct TransferRequest {
        uint256 id;
        address faculty;
        string fromInstitution;
        string toInstitution;
        uint256 creditsToTransfer;
        bool approved;
        bool executed;
        uint256 requestTime;
    }

    // State variables
    uint256 public institutionCount;
    uint256 public transferRequestCount;
    
    // Mappings
    mapping(string => Institution) public institutions;
    mapping(uint256 => TransferRequest) public transferRequests;
    mapping(address => string) public facultyInstitution;
    mapping(string => address[]) public institutionFaculty;

    // Events
    event InstitutionRegistered(string code, string name, address adminAddress);
    event InstitutionDeactivated(string code);
    event TransferRequested(uint256 requestId, address faculty, string fromInst, string toInst);
    event TransferApproved(uint256 requestId);
    event TransferExecuted(uint256 requestId);
    event FacultyMoved(address faculty, string fromInst, string toInst);

    constructor() {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(ADMIN_ROLE, msg.sender);
    }

    /**
     * @notice Register a new institution
     * @param _code Institution code
     * @param _name Institution name
     * @param _adminAddress Admin wallet address
     * @param _ledgerContract Address of the institution's credit ledger contract
     */
    function registerInstitution(
        string memory _code,
        string memory _name,
        address _adminAddress,
        address _ledgerContract
    ) external onlyRole(ADMIN_ROLE) {
        require(!institutions[_code].isActive, "Institution already exists");
        
        institutions[_code] = Institution({
            name: _name,
            code: _code,
            adminAddress: _adminAddress,
            ledgerContract: _ledgerContract,
            isActive: true,
            registrationTime: block.timestamp
        });

        institutionCount++;
        _grantRole(REGISTRAR_ROLE, _adminAddress);

        emit InstitutionRegistered(_code, _name, _adminAddress);
    }

    /**
     * @notice Register faculty with an institution
     * @param _faculty Faculty wallet address
     * @param _institutionCode Institution code
     */
    function registerFacultyWithInstitution(
        address _faculty,
        string memory _institutionCode
    ) external onlyRole(REGISTRAR_ROLE) {
        require(institutions[_institutionCode].isActive, "Institution not active");
        require(bytes(facultyInstitution[_faculty]).length == 0, "Faculty already registered");

        facultyInstitution[_faculty] = _institutionCode;
        institutionFaculty[_institutionCode].push(_faculty);
    }

    /**
     * @notice Request transfer of credits to another institution
     * @param _toInstitution Target institution code
     * @param _credits Credits to transfer
     */
    function requestTransfer(
        string memory _toInstitution,
        uint256 _credits
    ) external nonReentrant returns (uint256) {
        string memory fromInst = facultyInstitution[msg.sender];
        require(bytes(fromInst).length > 0, "Faculty not registered");
        require(institutions[_toInstitution].isActive, "Target institution not active");
        require(_credits > 0, "Credits must be positive");

        transferRequestCount++;
        uint256 requestId = transferRequestCount;

        transferRequests[requestId] = TransferRequest({
            id: requestId,
            faculty: msg.sender,
            fromInstitution: fromInst,
            toInstitution: _toInstitution,
            creditsToTransfer: _credits,
            approved: false,
            executed: false,
            requestTime: block.timestamp
        });

        emit TransferRequested(requestId, msg.sender, fromInst, _toInstitution);

        return requestId;
    }

    /**
     * @notice Approve a transfer request
     * @param _requestId Transfer request ID
     */
    function approveTransfer(uint256 _requestId) external onlyRole(REGISTRAR_ROLE) {
        TransferRequest storage request = transferRequests[_requestId];
        require(!request.approved, "Already approved");
        require(!request.executed, "Already executed");

        // Check if caller is admin of the target institution
        Institution storage toInst = institutions[request.toInstitution];
        require(toInst.adminAddress == msg.sender, "Not target institution admin");

        request.approved = true;
        emit TransferApproved(_requestId);
    }

    /**
     * @notice Execute an approved transfer
     * @param _requestId Transfer request ID
     */
    function executeTransfer(uint256 _requestId) external onlyRole(REGISTRAR_ROLE) nonReentrant {
        TransferRequest storage request = transferRequests[_requestId];
        require(request.approved, "Not approved");
        require(!request.executed, "Already executed");

        request.executed = true;
        
        // Update faculty institution
        facultyInstitution[request.faculty] = request.toInstitution;
        institutionFaculty[request.toInstitution].push(request.faculty);

        emit TransferExecuted(_requestId);
        emit FacultyMoved(request.faculty, request.fromInstitution, request.toInstitution);
    }

    /**
     * @notice Get institution details
     * @param _code Institution code
     */
    function getInstitution(string memory _code) external view returns (Institution memory) {
        return institutions[_code];
    }

    /**
     * @notice Get transfer request details
     * @param _requestId Request ID
     */
    function getTransferRequest(uint256 _requestId) external view returns (TransferRequest memory) {
        return transferRequests[_requestId];
    }

    /**
     * @notice Get faculty's current institution
     * @param _faculty Faculty address
     */
    function getFacultyInstitution(address _faculty) external view returns (string memory) {
        return facultyInstitution[_faculty];
    }

    /**
     * @notice Deactivate an institution
     * @param _code Institution code
     */
    function deactivateInstitution(string memory _code) external onlyRole(ADMIN_ROLE) {
        institutions[_code].isActive = false;
        emit InstitutionDeactivated(_code);
    }
}
