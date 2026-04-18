// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title SALFAccessControl
 * @notice Role-Based Access Control for the Secure Academic Ledger Framework
 * @dev Implements RBAC for Faculty, HoD, and Administrator roles
 */
contract SALFAccessControl is AccessControl, Pausable, ReentrancyGuard {
    // Role definitions
    bytes32 public constant FACULTY_ROLE = keccak256("FACULTY_ROLE");
    bytes32 public constant HOD_ROLE = keccak256("HOD_ROLE");
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant VALIDATOR_ROLE = keccak256("VALIDATOR_ROLE");
    bytes32 public constant REM_ROLE = keccak256("REM_ROLE"); // Record Evaluation Manager

    // Faculty registration structure
    struct FacultyInfo {
        string name;
        string department;
        string employeeId;
        string institution;
        uint256 registrationTimestamp;
        bool isActive;
        uint256 totalCredits;
    }

    // Department structure
    struct Department {
        string name;
        string code;
        address hodAddress;
        uint256 facultyCount;
        bool isActive;
    }

    // Mappings
    mapping(address => FacultyInfo) public facultyRegistry;
    mapping(string => Department) public departments;
    mapping(address => string) public facultyToDepartment;
    
    // Events
    event FacultyRegistered(address indexed facultyAddress, string name, string department, string employeeId);
    event FacultyDeactivated(address indexed facultyAddress);
    event FacultyReactivated(address indexed facultyAddress);
    event DepartmentCreated(string departmentCode, string name, address hodAddress);
    event HoDAssigned(string departmentCode, address newHoD);
    event CreditsUpdated(address indexed facultyAddress, uint256 newTotal);

    // Modifiers
    modifier onlyActiveFaculty() {
        require(facultyRegistry[msg.sender].isActive, "Faculty: Not an active faculty member");
        _;
    }

    modifier facultyExists(address _faculty) {
        require(bytes(facultyRegistry[_faculty].employeeId).length > 0, "Faculty: Does not exist");
        _;
    }

    constructor() {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(ADMIN_ROLE, msg.sender);
    }

    /**
     * @notice Register a new faculty member
     * @param _facultyAddress The wallet address of the faculty
     * @param _name Full name of the faculty
     * @param _department Department code
     * @param _employeeId Employee ID
     * @param _institution Institution name
     */
    function registerFaculty(
        address _facultyAddress,
        string memory _name,
        string memory _department,
        string memory _employeeId,
        string memory _institution
    ) external onlyRole(ADMIN_ROLE) whenNotPaused {
        require(bytes(facultyRegistry[_facultyAddress].employeeId).length == 0, "Faculty: Already registered");
        require(departments[_department].isActive, "Department: Does not exist or inactive");

        facultyRegistry[_facultyAddress] = FacultyInfo({
            name: _name,
            department: _department,
            employeeId: _employeeId,
            institution: _institution,
            registrationTimestamp: block.timestamp,
            isActive: true,
            totalCredits: 0
        });

        facultyToDepartment[_facultyAddress] = _department;
        departments[_department].facultyCount++;

        _grantRole(FACULTY_ROLE, _facultyAddress);

        emit FacultyRegistered(_facultyAddress, _name, _department, _employeeId);
    }

    /**
     * @notice Create a new department
     * @param _code Department code
     * @param _name Department name
     * @param _hodAddress HoD wallet address
     */
    function createDepartment(
        string memory _code,
        string memory _name,
        address _hodAddress
    ) external onlyRole(ADMIN_ROLE) whenNotPaused {
        require(!departments[_code].isActive, "Department: Already exists");

        departments[_code] = Department({
            name: _name,
            code: _code,
            hodAddress: _hodAddress,
            facultyCount: 0,
            isActive: true
        });

        _grantRole(HOD_ROLE, _hodAddress);

        emit DepartmentCreated(_code, _name, _hodAddress);
    }

    /**
     * @notice Assign a new HoD to a department
     * @param _departmentCode Department code
     * @param _newHoD New HoD wallet address
     */
    function assignHoD(
        string memory _departmentCode,
        address _newHoD
    ) external onlyRole(ADMIN_ROLE) whenNotPaused {
        require(departments[_departmentCode].isActive, "Department: Does not exist");

        address oldHoD = departments[_departmentCode].hodAddress;
        if (oldHoD != address(0)) {
            _revokeRole(HOD_ROLE, oldHoD);
        }

        departments[_departmentCode].hodAddress = _newHoD;
        _grantRole(HOD_ROLE, _newHoD);

        emit HoDAssigned(_departmentCode, _newHoD);
    }

    /**
     * @notice Deactivate a faculty member
     * @param _facultyAddress Faculty wallet address
     */
    function deactivateFaculty(
        address _facultyAddress
    ) external onlyRole(ADMIN_ROLE) facultyExists(_facultyAddress) {
        facultyRegistry[_facultyAddress].isActive = false;
        _revokeRole(FACULTY_ROLE, _facultyAddress);
        emit FacultyDeactivated(_facultyAddress);
    }

    /**
     * @notice Reactivate a faculty member
     * @param _facultyAddress Faculty wallet address
     */
    function reactivateFaculty(
        address _facultyAddress
    ) external onlyRole(ADMIN_ROLE) facultyExists(_facultyAddress) {
        facultyRegistry[_facultyAddress].isActive = true;
        _grantRole(FACULTY_ROLE, _facultyAddress);
        emit FacultyReactivated(_facultyAddress);
    }

    /**
     * @notice Update faculty credits (only callable by credit ledger contract)
     * @param _facultyAddress Faculty wallet address
     * @param _newTotal New total credits
     */
    function updateFacultyCredits(
        address _facultyAddress,
        uint256 _newTotal
    ) external onlyRole(VALIDATOR_ROLE) facultyExists(_facultyAddress) {
        facultyRegistry[_facultyAddress].totalCredits = _newTotal;
        emit CreditsUpdated(_facultyAddress, _newTotal);
    }

    /**
     * @notice Get faculty information
     * @param _facultyAddress Faculty wallet address
     */
    function getFacultyInfo(address _facultyAddress) external view returns (FacultyInfo memory) {
        return facultyRegistry[_facultyAddress];
    }

    /**
     * @notice Get department information
     * @param _departmentCode Department code
     */
    function getDepartmentInfo(string memory _departmentCode) external view returns (Department memory) {
        return departments[_departmentCode];
    }

    /**
     * @notice Check if an address is an active faculty member
     * @param _address Address to check
     */
    function isActiveFaculty(address _address) external view returns (bool) {
        return facultyRegistry[_address].isActive;
    }

    /**
     * @notice Pause the contract
     */
    function pause() external onlyRole(ADMIN_ROLE) {
        _pause();
    }

    /**
     * @notice Unpause the contract
     */
    function unpause() external onlyRole(ADMIN_ROLE) {
        _unpause();
    }

    /**
     * @notice Grant REM role to AI evaluation service
     * @param _remAddress Address of the REM service
     */
    function grantREMRole(address _remAddress) external onlyRole(ADMIN_ROLE) {
        _grantRole(REM_ROLE, _remAddress);
    }

    /**
     * @notice Grant Validator role
     * @param _validatorAddress Address of the validator (credit ledger contract)
     */
    function grantValidatorRole(address _validatorAddress) external onlyRole(ADMIN_ROLE) {
        _grantRole(VALIDATOR_ROLE, _validatorAddress);
    }
}
