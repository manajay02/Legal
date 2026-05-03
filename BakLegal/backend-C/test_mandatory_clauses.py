#!/usr/bin/env python3
"""
Test script to demonstrate the new mandatory clauses validation system.
Shows how to use the mandatory clauses mapping for the 10 domains.
"""

import json
from src.inference.compliance_checker_v2 import (
    MANDATORY_CLAUSES,
    validate_mandatory_clauses,
    get_mandatory_clauses_for_domain,
    get_all_mandatory_clauses_summary
)


def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def display_mandatory_clauses_summary():
    """Display summary of all mandatory clauses per domain"""
    print_section("SUMMARY: 10 DOMAINS WITH MANDATORY CLAUSES")
    
    summary = get_all_mandatory_clauses_summary()
    
    print(f"Total Domains Configured: {summary['total_domains']}\n")
    
    for domain_key, domain_info in summary['domains'].items():
        print(f"\n{domain_info['risk_level']} DOMAIN: {domain_info['domain_name']}")
        print(f"   Risk Level: {domain_info['risk_level']}")
        print(f"   Mandatory Clauses: {domain_info['total_mandatory']}")
        print(f"   Key Laws:")
        for law in domain_info['key_laws']:
            print(f"      • {law}")
        
        if domain_info['notes']:
            print(f"   Notes: {domain_info['notes']}")
        
        print(f"\n   Required Clauses:")
        for idx, clause in enumerate(domain_info['mandatory_clauses'], 1):
            print(f"      {idx}. {clause['id'].upper()}")
            print(f"         Act: {clause['act']}")
            print(f"         Rule: {clause['rule']}")
    
    print("\n")


def display_domain_details():
    """Display detailed information about each domain"""
    print_section("DETAILED DOMAIN CONFIGURATIONS")
    
    for domain_key, config in MANDATORY_CLAUSES.items():
        print(f"\nDomain: {domain_key.upper()}")
        print(f"Name: {config['domain_name']}")
        print(f"Risk Level: {config['risk_level']}")
        print(f"Total Mandatory Clauses: {config['total_mandatory']}")
        print(f"Mandatory Clause IDs: {', '.join(config['mandatory_clause_ids'])}")
        print(f"Key Laws: {', '.join(config['key_laws'])}")
        if 'notes' in config and config['notes']:
            print(f"Notes: {config['notes']}")


def test_validation():
    """Test the validate_mandatory_clauses function with sample contracts"""
    print_section("TESTING MANDATORY CLAUSES VALIDATION")
    
    # Test 1: Employment Contract (with most clauses)
    employment_contract = """
    EMPLOYMENT AGREEMENT
    
    This Employment Agreement ("Agreement") is made between XYZ Company (Employer) 
    and John Doe (Employee) on this 15th day of April 2024.
    
    1. IDENTIFICATION
    Employer: XYZ Company Private Limited, Registration No. PV-12345
    Employee: John Doe, NIC: 123-4567-8901
    
    2. POSITION AND COMMENCEMENT
    Position: Senior Software Engineer
    Department: Information Technology
    Commencement Date: 1st May 2024
    
    3. SALARY AND COMPENSATION
    Monthly Salary: LKR 150,000 (One Hundred Fifty Thousand Rupees)
    Payment Schedule: 5th of each month via bank transfer
    
    4. WORKING HOURS
    Normal working hours shall be 8 hours per day, Monday to Friday.
    Total: 40 hours per week
    
    5. LEAVE ENTITLEMENTS
    Annual Leave: 14 days per year
    Casual Leave: 7 days per year
    Sick Leave: 7 days per year
    
    6. EPF AND ETF CONTRIBUTIONS
    Employer will contribute 12% EPF + 3% ETF
    Employee will contribute 8% EPF
    
    7. TERMINATION
    Either party may terminate with 30 days written notice.
    Immediate termination allowed for just cause.
    """
    
    print("Test 1: EMPLOYMENT CONTRACT")
    result = validate_mandatory_clauses(employment_contract, "employment")
    
    print(f"Domain: {result['domain_name']}")
    print(f"Risk Level: {result['risk_level']}")
    print(f"Compliance: {result['found_count']}/{result['total_mandatory']} ({result['compliance_percentage']}%)")
    print(f"Status: {'✅ COMPLIANT' if result['is_compliant'] else '❌ NON-COMPLIANT'}")
    
    print(f"\nFound Clauses ({result['found_count']}):")
    for clause_id in result['found_clauses']:
        print(f"  ✅ {clause_id}")
    
    if result['missing_clauses']:
        print(f"\nMissing Clauses ({result['missing_count']}):")
        for clause_id in result['missing_clauses']:
            print(f"  ❌ {clause_id}")
    
    print(f"\nKey Laws to Comply With:")
    for law in result['key_laws']:
        print(f"  • {law}")
    
    # Test 2: Incomplete Contract
    print("\n" + "="*80)
    print("Test 2: INCOMPLETE RENTAL AGREEMENT")
    incomplete_rental = """
    TENANCY AGREEMENT
    
    This tenancy agreement is entered between ABC Properties (Landlord)
    and Jane Smith (Tenant).
    
    Rent: LKR 25,000 per month
    Premises: Apartment 5B, No. 123 Main Street, Colombo
    """
    
    result2 = validate_mandatory_clauses(incomplete_rental, "rental")
    
    print(f"Domain: {result2['domain_name']}")
    print(f"Compliance: {result2['found_count']}/{result2['total_mandatory']} ({result2['compliance_percentage']}%)")
    print(f"Status: {'✅ COMPLIANT' if result2['is_compliant'] else '❌ NON-COMPLIANT'}")
    
    if result2['missing_clauses']:
        print(f"\nMissing Critical Clauses:")
        for clause_id in result2['missing_clauses']:
            details = result2['clause_details'].get(clause_id, {})
            print(f"  ❌ {clause_id}")
            print(f"     Rule: {details.get('rule', 'N/A')}")


def test_domain_lookup():
    """Test domain lookup function"""
    print_section("TESTING DOMAIN LOOKUP")
    
    test_domains = ["employment", "property", "rental", "electronic", "partnership", "microfinance"]
    
    for domain in test_domains:
        domain_key, config = get_mandatory_clauses_for_domain(domain)
        if config:
            print(f"✅ {domain}")
            print(f"   Found as: {domain_key}")
            print(f"   Full Name: {config['domain_name']}")
            print(f"   Mandatory Clauses: {config['total_mandatory']}")
        else:
            print(f"❌ {domain} - NOT FOUND")


def main():
    """Main test runner"""
    print("\n" + "="*80)
    print("  MANDATORY CLAUSES VALIDATION SYSTEM - DEMO")
    print("  10 Domains with Comprehensive Mandatory Clause Mappings")
    print("="*80)
    
    # 1. Display summary
    display_mandatory_clauses_summary()
    
    # 2. Display detailed domain configurations
    display_domain_details()
    
    # 3. Test domain lookup
    test_domain_lookup()
    
    # 4. Test validation
    test_validation()
    
    print_section("TEST COMPLETED")
    print("All mandatory clause features have been successfully tested!")
    print("\nAvailable Functions:")
    print("  • validate_mandatory_clauses(contract_text, domain)")
    print("  • get_mandatory_clauses_for_domain(domain)")
    print("  • get_all_mandatory_clauses_summary()")
    print("  • check_mandatory_clauses(contract_text, domain)  [existing]")


if __name__ == "__main__":
    main()
