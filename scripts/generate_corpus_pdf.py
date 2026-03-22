#!/usr/bin/env python3
"""
Generates a realistic synthetic policy corpus (5 documents, ~250+ paragraphs).
Each document is self-contained; the IT Security Addendum intentionally
contradicts parts of the main handbook to test contradiction detection.
"""
from pathlib import Path
from fpdf import FPDF

RAW_DIR = Path("data/corpus/raw")


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

def _sanitize(text: str) -> str:
    """Replace Unicode chars that Helvetica can't render."""
    return (text
            .replace("\u2014", "--")   # em dash
            .replace("\u2013", "-")    # en dash
            .replace("\u2018", "'")    # left single quote
            .replace("\u2019", "'")    # right single quote
            .replace("\u201c", '"')    # left double quote
            .replace("\u201d", '"')    # right double quote
            .replace("\u2026", "...")  # ellipsis
            .replace("\u00a3", "GBP") # pound sign
            )


def _build_pdf(title: str, sections: list[tuple[str, str]], output_path: Path):
    """Build a PDF from section tuples (heading, body)."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=25)

    # Title page
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 60, "", ln=True)
    pdf.multi_cell(0, 12, _sanitize(title), align="C")
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 20, "", ln=True)
    pdf.cell(0, 10, "Version 2.0 - January 2025", align="C", ln=True)
    pdf.cell(0, 8, "Classification: INTERNAL", align="C", ln=True)

    # Content pages
    for heading, body in sections:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 14)
        pdf.multi_cell(0, 8, _sanitize(heading))
        pdf.ln(4)
        pdf.set_font("Helvetica", "", 11)

        for para in body.strip().split("\n\n"):
            clean = para.strip()
            if clean:
                pdf.multi_cell(0, 6, _sanitize(clean))
                pdf.ln(3)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output_path))
    print(f"[+] Generated {output_path} ({pdf.pages_count} pages)")


# ──────────────────────────────────────────────────────────────────────
# Document 1 — Internal Policy Handbook v2  (~80 paragraphs)
# ──────────────────────────────────────────────────────────────────────

HANDBOOK_SECTIONS = [
    ("1. Introduction and Scope",
     """This Internal Policy Handbook outlines the policies, procedures, and standards that govern employee conduct and organisational operations. It applies to all full-time, part-time, and contract employees.

All employees are expected to read and understand this handbook upon joining the company. Failure to comply with any policy herein may result in disciplinary action, up to and including termination of employment.

This handbook supersedes all previous versions of the employee policy manual. Any amendments will be communicated through official company channels and staff are required to acknowledge receipt of updates within 14 calendar days.

The policies contained in this document have been developed in consultation with legal counsel, the HR department, and senior management. They are reviewed annually and updated as necessary to reflect changes in legislation and best practice."""),

    ("2. Remote Work Policy",
     """Employees are permitted to work remotely up to 3 days per week, subject to line manager approval. Remote work arrangements must be documented using the Remote Work Agreement Form (HR-007) and renewed every 6 months.

All remote work must be performed from a secure, private location within the United Kingdom. Working from public spaces such as cafes, libraries, or co-working spaces on sensitive data is not permitted without prior authorisation from the IT Security team.

Employees working remotely must be available during core business hours (09:00-17:00 GMT) and must respond to communications within 30 minutes during these hours. Flexible scheduling outside core hours requires written approval from the department head.

Remote workers must use company-provided equipment and connect through the corporate VPN at all times. Use of personal devices for work purposes is governed by the BYOD policy (Section 13).

The company reserves the right to revoke remote work privileges with 5 working days notice if performance targets are not met or if security requirements are breached.

Remote workers are responsible for ensuring their home workspace meets health and safety requirements as outlined in the DSE (Display Screen Equipment) assessment policy. The company will provide ergonomic equipment upon request."""),

    ("3. Data Security and Classification Policy",
     """All company data must be classified according to the four-tier classification scheme: PUBLIC, INTERNAL, CONFIDENTIAL, and RESTRICTED. Data owners are responsible for assigning the correct classification level upon creation.

PUBLIC data may be freely shared outside the organisation. Examples include marketing materials, press releases, and published research papers.

INTERNAL data is for company-wide use and should not be shared externally without approval. Examples include internal memos, meeting minutes, organisational charts, and non-sensitive operational data.

CONFIDENTIAL data requires explicit authorisation for access and must be encrypted in transit and at rest. Examples include employee personal data, financial reports, customer lists, salary information, and strategic plans.

RESTRICTED data is the highest classification level and is limited to named individuals with a documented need-to-know. Examples include board-level discussions, M&A documentation, and security audit reports. RESTRICTED data must be stored only on approved encrypted systems.

Sharing of CONFIDENTIAL or RESTRICTED data externally requires written approval from the data owner and the Chief Information Security Officer. All external data transfers must use approved encrypted channels.

Data classification labels must be included in document headers and footers. Electronic files must include the classification in the filename suffix (e.g., report_Q4_CONFIDENTIAL.pdf).

Misclassification of data, whether intentional or negligent, constitutes a policy violation and will be investigated by the Data Governance team."""),

    ("4. Password and Authentication Policy",
     """All employees must use strong passwords for all company systems. Passwords must meet the following minimum requirements: at least 8 characters in length, containing at least one uppercase letter, one lowercase letter, one number, and one special character.

Passwords must be changed every 90 days. The system will enforce this automatically by prompting users 14 days before expiration. Employees who fail to change their password by the deadline will be locked out until IT Support resets their credentials.

Password reuse is prohibited for the last 12 passwords. Common passwords, dictionary words, and passwords containing the user's name or employee ID are blocked by the password policy engine.

Multi-factor authentication (MFA) is mandatory for all remote access, VPN connections, and access to CONFIDENTIAL or RESTRICTED systems. MFA tokens must be registered with IT Security before first use.

Sharing passwords with colleagues, contractors, or third parties is strictly prohibited, regardless of seniority or business justification. Each user account is tied to a single individual for audit purposes.

After 5 consecutive failed login attempts, the account will be locked for 30 minutes. After 10 consecutive failures within 24 hours, the account is permanently locked and requires IT Security intervention.

Employees must not write passwords on paper, sticky notes, or store them in unencrypted digital files. Use of the company-approved password manager (currently LastPass Enterprise) is mandatory."""),

    ("5. Access Control and Authorisation",
     """Access to CONFIDENTIAL and RESTRICTED systems is granted on a need-to-know basis, approved by the data owner and verified by IT Security. All access requests must be submitted via the Access Request Portal (ITS-003).

Access privileges are reviewed quarterly by the Access Review Board. Unused accounts (no login for 60 days) are automatically disabled. Accounts of departing employees are suspended on their last working day and deleted after 90 days.

Privileged accounts (administrator, root, service accounts) require additional controls including enhanced logging, session recording, and bi-annual access recertification. Privileged access must not be used for routine tasks.

External contractors and consultants are granted temporary access with a maximum duration of 90 days. Extensions require re-approval from the sponsoring department and IT Security.

Third-party access to company systems must be governed by a signed Non-Disclosure Agreement (NDA) and a Data Processing Agreement (DPA) where applicable.

Segregation of duties must be maintained: no single individual should have end-to-end control over a critical process without compensating controls. IT Security conducts annual SoD reviews."""),

    ("6. Incident Response and Data Breach Procedures",
     """All suspected security incidents must be reported to the Security Operations Centre (SOC) within 1 hour of discovery via email (soc@company.com) or the incident hotline (ext. 9999). Failure to report promptly is itself a policy violation.

The Incident Response Team (IRT) will triage all reported incidents within 4 hours and classify them as P1 (Critical), P2 (High), P3 (Medium), or P4 (Low) based on impact and scope.

P1 incidents (confirmed data breach, ransomware, system compromise) trigger the Major Incident Protocol: automatic escalation to the CISO, legal counsel, and the board. External communication is managed exclusively by the Communications team.

All P1 and P2 incidents require a Root Cause Analysis (RCA) report within 10 working days. The RCA must identify contributing factors, remediation steps, and preventive measures. Lessons learned are shared anonymously at the monthly Security Forum.

In the event of a personal data breach, the Data Protection Officer (DPO) must be notified immediately. The DPO will determine whether notification to the ICO (Information Commissioner's Office) is required within the statutory 72-hour window.

All employees must cooperate fully with incident investigations. Attempting to conceal, minimise, or delay reporting of a security incident will be treated as gross misconduct.

Incident logs are retained for 7 years for audit and regulatory compliance purposes."""),

    ("7. Training and Awareness Requirements",
     """All employees must complete mandatory security awareness training annually. New starters must complete the training within 30 days of joining. The training covers phishing recognition, data handling, password hygiene, and incident reporting.

Department heads are responsible for ensuring 100% completion rates within their teams. Completion status is tracked via the Learning Management System (LMS) and reported to the Security Committee quarterly.

Employees handling CONFIDENTIAL or RESTRICTED data must complete enhanced data protection training, including GDPR fundamentals and sector-specific compliance requirements.

Phishing simulation exercises are conducted monthly. Employees who fail two consecutive simulations are required to attend a mandatory 2-hour remedial workshop facilitated by IT Security.

Training content is updated annually by the Security Awareness team in collaboration with HR. Feedback from previous programmes and emerging threat intelligence inform content revisions.

Managers are required to complete an additional leadership security module covering their responsibilities for team compliance, access review, and incident escalation."""),

    ("8. Acceptable Use of IT Resources",
     """Company IT resources, including email, internet, software, and hardware, are provided for business purposes. Limited personal use is permitted provided it does not interfere with work duties, consume excessive bandwidth, or create security risks.

Installation of unauthorised software on company devices is prohibited. All software must be deployed through the company software catalogue, managed by the IT Service Desk.

USB storage devices may be used only with prior approval from IT Security and must be encrypted using company-approved encryption tools. Unencrypted USB devices are blocked by endpoint protection software.

Company email must not be used for personal financial transactions, political campaigning, religious solicitation, or distribution of offensive material. All email is subject to monitoring and archiving for compliance purposes.

Internet browsing is filtered by category. Access to known malicious sites, gambling platforms, adult content, and anonymous proxy services is blocked. Employees may request category exceptions through the IT Service Desk with business justification.

Circumventing security controls, including proxy bypass, VPN tunnelling to external services, or disabling endpoint protection, constitutes a serious policy violation.

Employees must immediately report any suspicious emails, attachments, or links to the SOC. If in doubt, do not click — forward the message to phishing@company.com.

Company-provided mobile devices must be enrolled in the Mobile Device Management (MDM) solution. Remote wipe capability is enabled on all managed devices."""),

    ("9. Physical Security",
     """All office locations must maintain appropriate physical security controls including CCTV, access badge systems, and reception staffing during business hours.

Employee badges must be worn visibly at all times within company premises. Tailgating — allowing unauthorised individuals to enter through controlled doors — is prohibited. Report tailgating incidents to Facilities immediately.

The server room and data centre areas are classified as Restricted Zones. Access is limited to authorised IT Operations staff and requires both badge access and biometric verification.

Visitors to the office must sign in at reception, receive a visitor badge, and be escorted by their host at all times. Visitors must never be left unattended in any area. Visitor badges must be returned upon departure.

Visitors are never permitted in Restricted Zones (server rooms, data centres, security operations centre) under any circumstances, regardless of the visitor's seniority or purpose of visit.

Clean desk policy is mandatory in all open-plan areas. At the end of each working day, employees must: clear all documents from desks, lock filing cabinets, lock computer screens, and secure any removable media in locked storage.

Sensitive documents must be disposed of using cross-cut shredders provided on each floor. Regular waste bins must not be used for any documents containing company data.

Building access outside normal business hours (07:00-20:00) requires pre-authorisation from the department head and must be logged with Facilities."""),

    ("10. Record Retention and Disposal",
     """Company records must be retained in accordance with the Record Retention Schedule published by the Legal department. The retention schedule specifies minimum and maximum retention periods by document category.

Financial records: minimum 7 years from the end of the financial year. Employee personnel records: minimum 6 years after employment ends. Contracts: 6 years after expiry. Board minutes: indefinite retention.

Health and safety records, including accident reports and risk assessments, must be retained for 40 years from the date of the event.

Electronic records must be stored in approved document management systems with appropriate access controls and audit trails. Local storage of records on desktop computers or personal drives is not permitted for compliance-critical documents.

When the retention period expires, records must be disposed of securely. Paper records are shredded by the approved disposal contractor. Electronic records are deleted using certified data sanitisation tools that meet DoD 5220.22-M standards.

Ad hoc deletion of records outside the retention schedule is prohibited unless authorised by the Legal department. In the event of litigation or regulatory investigation, a legal hold may be placed to suspend normal disposal.

All destruction activities must be logged, including: document type, classification, volume, method of destruction, date, and the name of the responsible employee."""),

    ("11. Cloud Services and Storage",
     """Only cloud storage services approved by the IT department may be used for company data. The current approved services are Microsoft 365 (SharePoint, OneDrive), the corporate AWS tenancy, and Confluence for documentation.

Use of personal cloud storage services (Google Drive, Dropbox, iCloud, etc.) for company data is strictly prohibited, regardless of the classification level.

All data stored in cloud services must comply with the Data Classification Policy (Section 3). RESTRICTED data may only be stored in the dedicated encrypted zone within the corporate AWS tenancy.

Cloud services must be configured by IT Operations in accordance with security baselines. Self-provisioning of cloud resources by business users is not permitted without IT Security approval.

Backup and disaster recovery for cloud-hosted data is managed by IT Operations. Business-critical data is backed up daily with 30-day retention. Recovery Point Objective (RPO): 4 hours. Recovery Time Objective (RTO): 8 hours.

Cloud provider selection and onboarding requires a Security Assessment conducted by IT Security, covering: data residency, encryption, access controls, certifications (SOC 2, ISO 27001), and incident notification commitments."""),

    ("12. Compliance and Consequences",
     """All employees are expected to comply with the policies in this handbook. Ignorance of a policy is not an acceptable defence — employees are responsible for reading and understanding all relevant policies.

Policy violations will be investigated by the relevant department in collaboration with HR and, where appropriate, Legal. Investigations will follow the Disciplinary Procedure outlined in the Employee Handbook.

Minor violations (first occurrence, low impact, no malicious intent) will typically result in a verbal warning and mandatory refresher training.

Moderate violations (repeat offences, negligent data handling, failure to follow procedures) may result in a written warning, temporary access restrictions, and enhanced monitoring.

Serious violations (intentional data theft, deliberate security bypass, harassment, fraud) will result in immediate suspension pending investigation. Confirmed serious violations may lead to summary dismissal and, where applicable, criminal referral.

Managers are responsible for enforcing policy compliance within their teams. Failure to address known violations by direct reports may itself constitute a policy violation.

An annual compliance audit is conducted by Internal Audit. Departments with significant non-compliance findings receive enhanced oversight and must submit remediation plans within 30 days.

The Compliance Committee, chaired by the Chief Compliance Officer, reviews policy effectiveness quarterly and recommends amendments based on audit findings, incident trends, and regulatory changes."""),

    ("13. Bring Your Own Device (BYOD) Policy",
     """Employees may use personal devices (smartphones, tablets, laptops) for work purposes subject to the conditions in this section. BYOD enrolment requires completion of the BYOD Agreement Form (IT-012) and device registration with IT Security.

All BYOD devices must be enrolled in the company Mobile Device Management (MDM) solution. MDM enables remote data wipe of company data containers without affecting personal data.

BYOD devices must meet minimum security requirements: current operating system version (within 2 major releases), device encryption enabled, screen lock with PIN/biometric, no jailbreaking or rooting.

Company data on BYOD devices is segregated in a secure container managed by the MDM solution. Personal apps cannot access data within the secure container.

The company reserves the right to remotely wipe the secure container if the device is lost, stolen, or if the employee leaves the company. Personal data outside the container is not affected.

BYOD devices must not be used to store RESTRICTED data under any circumstances. CONFIDENTIAL data may only be accessed (not downloaded) through the secure container.

Employees are responsible for the physical security of their personal devices. Lost or stolen devices must be reported to IT Security within 2 hours."""),

    ("14. Travel and International Working Policy",
     """Employees travelling internationally on company business must comply with additional security requirements. Travel to high-risk countries (list maintained by IT Security) requires pre-approval from the CISO.

A clean/loaner device must be used for travel to high-risk countries. Employees must not take their primary work device. Loaner devices are available from IT Security with 5 working days notice.

All data on travel devices must be encrypted with full-disk encryption. Sensitive data should be accessed via cloud services rather than stored locally on the device.

Public Wi-Fi networks must not be used for any company business. The corporate VPN must be active at all times when using hotel or conference Wi-Fi. Mobile hotspot is the preferred connection method.

Upon return from high-risk travel, loaner devices must be returned to IT Security for forensic inspection before being reissued. Any personal devices used during travel should be submitted for voluntary scanning.

Border control access to devices: if authorities request to inspect device contents, employees should comply but report the inspection to the Legal team and IT Security immediately upon return.

Employees must avoid discussing CONFIDENTIAL or RESTRICTED information in public settings (hotel lobbies, airports, restaurants) where conversations could be overheard."""),

    ("15. Software Development and Change Management",
     """All software changes to production systems must follow the Change Management process defined in ITIL Change Management Procedure (ITSM-005).

Standard changes (pre-approved, low-risk) can proceed through the automated deployment pipeline. Normal changes require a Change Request (CR) approved by the Change Advisory Board (CAB) at their weekly meeting.

Emergency changes bypass the normal CAB process but require retrospective approval within 48 hours. The Emergency Change Manager (on-call IT Operations lead) must authorise all emergency changes before implementation.

All code changes must undergo peer review before merging. The minimum review requirement is one independent reviewer for standard changes and two reviewers for changes affecting security-sensitive components.

Deployment to production occurs only during approved maintenance windows (Tuesdays and Thursdays, 22:00-02:00 GMT) unless an emergency change is authorised. Deployments must include a rollback plan.

Security-sensitive code changes (authentication, authorisation, encryption, data handling) require additional review by a member of the Security Engineering team before approval.

All changes are tracked in the ITSM tool with full audit trail: requester, approver(s), implementation date, test results, and post-deployment verification."""),

    ("16. Anti-Bribery and Corruption Policy",
     """The company has a zero-tolerance policy towards bribery and corruption in all its forms. This policy applies to all employees, directors, contractors, and agents acting on behalf of the company.

Employees must not offer, promise, give, request, or accept any bribe, whether in cash, gifts, hospitality, or other inducements, in connection with company business.

Gifts and hospitality may be given or received only if they are reasonable, proportionate, and given openly. All gifts or hospitality with a value exceeding 50 GBP must be declared in the Gifts and Hospitality Register and approved by the Line Manager and Compliance team.

Facilitation payments — small payments to officials to speed up routine processes — are prohibited regardless of local custom or practice. Any request for such a payment must be reported to the Legal team.

Due diligence must be conducted on all third-party partners, agents, and intermediaries before engagement. Enhanced due diligence is required for partners in countries with a Corruption Perception Index score below 50.

Employees who suspect bribery or corruption should report their concerns through the confidential whistleblowing hotline (0800-ETHICS) or to the Ethics Committee. Reports can be made anonymously. The company prohibits retaliation against whistleblowers."""),

    ("17. Environmental and Sustainability Policy",
     """The company is committed to minimising its environmental impact and operating sustainably. This policy sets out the environmental standards expected of all employees and departments.

All offices must participate in the company recycling programme, separating waste into general, paper, plastics, and electronic waste streams. Electronic waste must be disposed of through the approved WEEE disposal contractor.

Energy conservation measures include: automatic light sensors in meeting rooms and corridors, default screen timeout of 5 minutes on all company devices, and heating/cooling set to 20-22 degrees Celsius during business hours.

Business travel should be minimised where video conferencing is a viable alternative. When travel is necessary, rail transport is preferred over air travel for domestic journeys under 300 miles.

Each department must appoint a Sustainability Champion responsible for promoting environmental awareness and tracking departmental energy and waste metrics.

An annual Environmental Impact Report is published by the Facilities team, covering carbon emissions, waste volumes, and progress against sustainability targets."""),
]


# ──────────────────────────────────────────────────────────────────────
# Document 2 — IT Security Addendum  (~50 paragraphs, with contradictions)
# ──────────────────────────────────────────────────────────────────────

ADDENDUM_SECTIONS = [
    ("1. Purpose and Scope",
     """This IT Security Addendum provides supplementary security guidance issued by the Chief Information Security Officer. Where this addendum conflicts with existing policy documents, the addendum takes precedence as the most recently published guidance.

This addendum applies to all employees, contractors, temporary staff, and third-party users of company IT systems. Compliance is mandatory and will be audited quarterly by the IT Security team.

This addendum was developed following the annual security risk assessment (December 2024) and reflects updated threat landscape analysis, penetration testing findings, and regulatory changes."""),

    ("2. Enhanced Password Requirements",
     """Following a recent security audit, the following enhanced password requirements supersede Section 4 of the Internal Policy Handbook. All passwords must now be a minimum of 12 characters in length (increased from 8 characters).

Password rotation period is reduced to 30 days for all users (previously 90 days). Privileged accounts must rotate passwords every 14 days. Automated rotation is enforced through the Identity Management platform.

Passphrases are now accepted and encouraged as an alternative to traditional passwords. A passphrase must contain at least 4 words and a minimum of 20 characters. The first character of each word must be capitalised.

Failed login threshold is reduced to 3 attempts (from 5), after which the account is locked for 60 minutes. IT Security may override this lockout for critical operational accounts on a case-by-case basis."""),

    ("3. Network Access and Remote Connectivity",
     """Access to company systems from public Wi-Fi networks is now strictly prohibited, including when using VPN. Employees must use either the corporate network, a company-provided mobile hotspot, or a personal mobile data connection.

All remote access sessions are limited to a maximum of 8 hours and require re-authentication. Session recording is enabled for all privileged remote access sessions.

Split-tunnel VPN configurations are no longer permitted. All network traffic from company devices must route through the corporate VPN, regardless of destination.

Network access from personal devices is restricted to the Guest network segment, which provides internet-only access with no connectivity to internal systems. Access to internal systems from personal devices requires BYOD enrolment (Section 13 of the handbook).

Geographic access restrictions are now enforced: access from outside the UK, EU, and US requires pre-authorisation from IT Security, submitted at least 72 hours in advance."""),

    ("4. USB and Removable Media",
     """Effective immediately, USB storage devices are prohibited on all company endpoints. This supersedes the previous policy permitting encrypted USB devices with IT Security approval.

This prohibition includes USB flash drives, external hard drives, SD cards, and any other removable storage media. USB ports on company devices are disabled via endpoint protection policy.

Exceptions may be granted only by the CISO for documented operational requirements. Exception requests must include business justification, risk assessment, and proposed compensating controls. Approved exceptions are valid for a maximum of 30 days.

Data transfer between systems must use approved secure channels: SFTP, encrypted email, or approved cloud storage services. Physical media transfer of any kind requires CISO approval.

USB peripherals (keyboards, mice, headsets) remain permitted but must be non-storage devices. IT Security maintains an approved peripherals list."""),

    ("5. Visitor Access to Secure Areas",
     """Visitors may be granted temporary escorted access to secure areas, including server rooms, under the following conditions: the visit is pre-approved by the IT Operations Manager, a documented business justification is provided, and the visitor is escorted by an authorised employee at all times.

This supersedes the blanket prohibition on visitor access to Restricted Zones. The updated policy recognises that certain maintenance activities (HVAC servicing, electrical inspections, fire safety assessments) require third-party access.

Visitor access to server rooms is limited to a maximum of 4 hours per visit. All visitor activities in Restricted Zones must be logged in real-time by the escort using the Visitor Activity Log (FA-008).

Visitors must not bring electronic devices (phones, laptops, cameras) into Restricted Zones without prior written approval from the CISO. All approved devices must be inspected and logged before entry.

Unescorted visitor access is never permitted under any circumstances, regardless of the visitor's role or purpose. Escorts must remain within visual line of sight of the visitor at all times."""),

    ("6. Training Frequency",
     """Security awareness training must be completed quarterly by all employees, superseding the annual requirement in the handbook. Quarterly training modules will be shorter (30 minutes each) but more frequent to improve retention.

Each quarterly module will focus on a specific topic: Q1 — Phishing and Social Engineering, Q2 — Data Handling and Classification, Q3 — Incident Response and Reporting, Q4 — Physical Security and Clean Desk.

Phishing simulation frequency is increased to weekly. Results are tracked per-department and published on the security dashboard. Departments consistently scoring below 90% pass rate receive targeted intervention.

Employees who fail any phishing simulation must complete an additional 15-minute micro-learning module within 48 hours. Failure to complete remedial training within the deadline results in temporary email quarantine.

New starters must complete the onboarding security module within 7 days (reduced from 30 days). The module includes a practical assessment that must be passed with a score of 80% or higher."""),

    ("7. Data Sharing Approval Process",
     """For operational efficiency, sharing of INTERNAL-classified data with approved external partners does not require manager approval, superseding the general requirement in Section 3 of the handbook.

A list of approved external partners is maintained by the Procurement team and published on the company intranet. Partners on this list have signed appropriate NDAs and DPAs.

Sharing of CONFIDENTIAL data externally always requires dual approval: the data owner and the CISO. Automated workflows in the DLP (Data Loss Prevention) system facilitate rapid approvals with target response time of 4 hours.

All external data sharing, regardless of classification, must be logged in the Data Sharing Register maintained by the Data Governance team. The register records: date, data description, classification, recipient, method of transfer, and approver.

RESTRICTED data may never be shared externally without board-level approval. Digital sharing of RESTRICTED data requires the use of the company's secure data room solution with full audit logging."""),

    ("8. Encryption Standards Update",
     """Encryption of sensitive data at rest is mandatory for all CONFIDENTIAL and RESTRICTED data, using AES-256 or equivalent approved algorithms. This supersedes the more general encryption requirements in the handbook.

Data in transit must be protected using TLS 1.3 or higher. TLS 1.2 is permitted only for legacy systems with a documented exception, which must be remediated within 6 months.

Full-disk encryption is mandatory on all company endpoints (laptops, desktops, mobile devices). BitLocker (Windows) and FileVault (macOS) are the approved solutions. Recovery keys must be escrowed to the central key management system.

Email encryption is required for all emails containing CONFIDENTIAL or RESTRICTED data. The approved solution (Microsoft 365 OME) provides automatic encryption based on sensitivity labels.

Encryption key management must follow the Key Management Standard (ITS-009). Keys must be rotated annually, and key custodians must be registered with IT Security."""),

    ("9. Staff Attendance and Office Presence",
     """All employees are expected to maintain a minimum of 5 days per week in-office presence, effective from 1 February 2025. This supersedes the remote work provisions in Section 2 of the handbook.

Exceptions to the in-office requirement will be considered on a case-by-case basis by the HR Director in consultation with the employee's line manager. Medical exemptions require occupational health documentation.

Hot-desking is the default arrangement for all employees. Personal desk assignment is available only for employees with documented ergonomic or medical requirements.

Core presence hours are 09:30-15:30. Arrival and departure flexibility is permitted outside these hours provided the standard 37.5-hour week is worked. Time tracking is managed through the corporate HRIS.

Employees with existing remote work agreements (pre-dating this addendum) will transition to the new attendance requirement over a 3-month grace period, ending 30 April 2025."""),

    ("10. Endpoint Detection and Response",
     """All company endpoints must have the approved EDR (Endpoint Detection and Response) agent installed and running. Currently, the approved solution is CrowdStrike Falcon.

Employees must not disable, uninstall, or interfere with the EDR agent. Tampering with endpoint security software is treated as a serious policy violation.

The EDR system monitors for suspicious activities including: unusual process execution, lateral movement, privilege escalation, unauthorised network connections, and data exfiltration attempts.

Alerts from the EDR system are triaged by the SOC. High-severity alerts trigger automatic device isolation pending investigation. Affected employees will be contacted by the SOC for interview.

Monthly endpoint compliance reports are generated and shared with department heads. Departments with less than 95% compliance on EDR deployment receive a formal non-compliance notice."""),

    ("11. Secure Software Development",
     """All development teams must integrate security testing into their CI/CD pipelines. Static Application Security Testing (SAST) must be run on every Pull Request. Builds with Critical or High severity findings must not be merged.

Dynamic Application Security Testing (DAST) must be run at least weekly against staging environments. Findings are tracked in the vulnerability management platform and must be remediated within SLA.

Dependency scanning must be enabled in all repositories. Libraries with known Critical vulnerabilities must be updated within 48 hours, High within 5 working days.

Secrets management: hard-coding of credentials, API keys, or certificates in source code is prohibited. All secrets must be managed through the approved vault solution.

Security architecture review is required for all new services and significant changes to existing services. Review requests must be submitted at least 10 working days before the planned deployment."""),

    ("12. Vulnerability Management",
     """Critical vulnerabilities must be patched within 24 hours of publication. High-severity vulnerabilities must be patched within 7 days. Medium and Low vulnerabilities must be patched within 30 days.

Patching schedules are maintained by IT Operations. Emergency patches outside the normal maintenance window require Emergency Change authorisation.

Vulnerability scanning of all internet-facing systems occurs daily. Internal network scanning occurs weekly. Results feed into the vulnerability management dashboard.

Systems that cannot be patched within SLA must have a documented risk acceptance, signed by the system owner and the CISO. Compensating controls must be implemented as specified by IT Security.

External penetration testing is conducted annually by an approved third-party provider. Internal red team exercises are conducted quarterly. Findings from both are tracked to remediation."""),
]


# ──────────────────────────────────────────────────────────────────────
# Document 3 — HR Procedures Manual  (~40 paragraphs)
# ──────────────────────────────────────────────────────────────────────

HR_SECTIONS = [
    ("1. Purpose",
     """This HR Procedures Manual provides operational guidance for managers and HR Business Partners on key people processes. It supplements the Employee Handbook and should be read in conjunction with company policies.

All procedures described herein have been reviewed by the Legal team for compliance with UK employment law, including the Employment Rights Act 1996, the Equality Act 2010, and the Working Time Regulations 1998."""),

    ("2. Recruitment and Selection",
     """All vacancies must be approved by the department budget holder and HR before advertising. The Recruitment Authorisation Form (HR-001) must be completed and signed.

Job descriptions must be reviewed by HR for compliance with equal opportunities legislation before publication. All roles must specify essential and desirable criteria based on objective, job-related requirements.

Interview panels must include at least two interviewers, one of whom must have completed Unconscious Bias Training within the last 12 months. Panel composition should reflect diversity where possible.

All candidates must undergo right-to-work verification before their start date. Offers of employment are conditional upon satisfactory completion of background checks, reference verification, and, where applicable, DBS (Disclosure and Barring Service) checks.

The standard offer process involves: verbal offer by the Hiring Manager, formal written offer from HR within 2 working days, and a 5-working-day acceptance window."""),

    ("3. Onboarding",
     """All new starters must receive their onboarding pack at least 3 working days before their start date. The pack includes: contract of employment, IT equipment request form, building access application, and pre-reading materials.

First-day induction is facilitated by HR and includes: company overview, health and safety briefing, IT orientation, security awareness training enrolment, and introductions to key contacts.

New starters must complete mandatory training modules within their first 30 days: Security Awareness, Data Protection (GDPR), Anti-Bribery, Health and Safety, and Equality and Diversity.

Line managers must schedule a structured 90-day onboarding plan, including weekly 1:1 meetings during the first month and fortnightly thereafter. A formal probation review is conducted at 3 months and 6 months.

New employees are assigned a buddy from within their team who serves as an informal point of contact for questions and cultural orientation during the first 3 months."""),

    ("4. Performance Management",
     """Annual performance reviews are conducted in March each year, covering the previous financial year (April-March). Mid-year reviews are conducted in September.

Performance is assessed against three dimensions: Role Objectives (50% weighting), Competency Behaviours (30% weighting), and Development Goals (20% weighting).

All objectives must be SMART (Specific, Measurable, Achievable, Relevant, Time-bound). A minimum of 3 and maximum of 5 objectives should be set per review cycle.

Performance ratings use a 5-point scale: 1 (Exceptional), 2 (Exceeds Expectations), 3 (Meets Expectations), 4 (Partially Meets), 5 (Does Not Meet). Rating calibration sessions are held at department level before finalisation.

Employees rated 4 or 5 are placed on a Performance Improvement Plan (PIP) with clear targets, support measures, and a review period of 60-90 days. Failure to improve may result in further action under the Disciplinary Procedure."""),

    ("5. Absence Management",
     """All sickness absences must be reported to the line manager by 09:30 on the first day of absence. Self-certification is accepted for absences of up to 7 calendar days. A GP fit note is required from the 8th calendar day.

Absence is monitored using the Bradford Factor. Employees reaching a Bradford Factor score of 200 will receive a formal absence review meeting. A score of 500 triggers a written warning.

Long-term sickness (28+ consecutive calendar days) requires referral to Occupational Health. Return-to-work plans must be agreed between the employee, line manager, HR, and OH, with reasonable adjustments considered under the Equality Act 2010.

Annual leave entitlement is 25 days plus bank holidays. Employees with 5+ years of service receive an additional day per year, up to a maximum of 30 days. Carry-over of up to 5 unused days is permitted with line manager approval.

Requests for unpaid leave, sabbaticals, or career breaks must be submitted to HR at least 3 months in advance. Approval is at the discretion of the department head and HR Director."""),

    ("6. Disciplinary Procedure",
     """The disciplinary procedure applies to all employees who have completed their probation period. Probationary employees are subject to a separate process as outlined in their contract of employment.

The disciplinary procedure follows ACAS guidelines and consists of: investigation, disciplinary hearing, decision, and right of appeal. Employees have the right to be accompanied by a trade union representative or work colleague at all formal stages.

Disciplinary sanctions may include: Stage 1 — verbal warning (valid 6 months), Stage 2 — first written warning (valid 12 months), Stage 3 — final written warning (valid 18 months), Stage 4 — dismissal with notice.

Gross misconduct may result in summary dismissal without prior warnings. Examples include: theft, fraud, violent behaviour, deliberate damage to company property, serious breach of security policies, and discrimination or harassment.

All disciplinary records are maintained in the employee's personal file for the duration of the sanction. Expired warnings are retained but not used as active precedents unless there is a pattern of similar behaviour."""),

    ("7. Grievance Procedure",
     """Employees who wish to raise a formal grievance should submit their complaint in writing to the HR Business Partner for their department. The grievance will be acknowledged within 2 working days.

A grievance hearing will be scheduled within 10 working days of receipt. The hearing will be conducted by a manager who is not involved in the matter being grieved and who has been trained in grievance resolution.

The outcome of the grievance hearing will be communicated in writing within 5 working days. Possible outcomes include: grievance upheld (with specified remedial action), grievance partially upheld, or grievance not upheld.

Employees have the right to appeal the grievance decision within 10 working days. The appeal will be heard by a more senior manager not previously involved. The appeal decision is final.

The company encourages informal resolution of workplace disputes before formal grievance procedures are invoked. Mediation services are available through the HR team."""),

    ("8. Leaving the Company",
     """Employees resigning from the company must provide notice in writing as specified in their contract. The standard notice period is: 1 month for employees below senior management, 3 months for senior managers and directors.

Exit interviews are conducted by HR for all departing employees. Participation is voluntary but encouraged. Exit interview data is analysed quarterly to identify trends in attrition and areas for improvement.

During the notice period, employees must: return all company property (laptop, badge, phone, documents), complete knowledge transfer activities as directed by their manager, and cooperate with handover plans.

IT access is revoked at 17:00 on the employee's last working day. Building access badges must be returned to reception. Any company data on personal devices must be deleted, and BYOD containers are remotely wiped.

Final salary payments, including accrued holiday and any outstanding expenses, are processed in the next scheduled payroll run following the leaving date."""),
]


# ──────────────────────────────────────────────────────────────────────
# Document 4 — Data Protection Impact Assessment Guide  (~30 paragraphs)
# ──────────────────────────────────────────────────────────────────────

DPIA_SECTIONS = [
    ("1. Introduction to DPIA",
     """A Data Protection Impact Assessment (DPIA) is a process designed to identify and minimise data protection risks arising from a project, system, or process that involves personal data.

Under the UK GDPR, a DPIA is mandatory when processing is likely to result in a high risk to the rights and freedoms of individuals. This includes: systematic monitoring of publicly accessible areas, large-scale processing of special category data, and automated decision-making with legal effects.

Even when a DPIA is not legally required, the company policy is to conduct one for any new system or significant change that processes personal data, to demonstrate accountability and compliance with data protection principles."""),

    ("2. When is a DPIA Required?",
     """A DPIA must be conducted before the processing begins. It should be initiated at the planning stage of any project to allow findings to influence the design.

Mandatory DPIA triggers include: introduction of new technology for processing personal data, processing special categories of data on a large scale, systematic monitoring of employees, data sharing with new third parties, and cross-border data transfers.

The Data Protection Officer (DPO) must be consulted on all DPIAs. The DPO reviews the assessment for completeness, adequacy of risk mitigation measures, and compliance with the data protection policy.

If a DPIA identifies residual high risks that cannot be mitigated, the processing must not proceed without consultation with the Information Commissioner's Office (ICO) under Article 36 of the UK GDPR."""),

    ("3. DPIA Process",
     """Step 1 — Describe the Processing: Document what personal data is collected, from whom, for what purpose, how it is stored, who has access, and how long it is retained. Include data flow diagrams where helpful.

Step 2 — Assess Necessity and Proportionality: Evaluate whether the processing is necessary for the stated purpose and whether less intrusive alternatives exist. Document the lawful basis for processing.

Step 3 — Identify and Assess Risks: Consider risks to individuals including: unauthorised access, data loss, inaccuracy, unfair processing, loss of control, and discrimination. Rate each risk by likelihood and severity.

Step 4 — Identify Measures to Mitigate Risk: For each identified risk, document specific technical and organisational measures to reduce the risk to an acceptable level. Examples include encryption, access controls, pseudonymisation, and training.

Step 5 — Record Outcomes: Complete the DPIA template (DP-001), recording all findings, decisions, and mitigations. The completed DPIA must be reviewed and signed by the project owner, the DPO, and the Information Asset Owner.

Step 6 — Review and Update: DPIAs are living documents and must be reviewed when the processing changes, when new risks emerge, or at least annually. Material changes require a DPIA addendum rather than a completely new assessment."""),

    ("4. DPIA Template Fields",
     """The DPIA template (DP-001) contains the following sections: Project Overview, Data Items and Categories, Lawful Basis, Data Subjects, Data Flows, Retention Periods, Third-Party Sharing, International Transfers, Security Measures, Risk Assessment Matrix, Mitigation Measures, DPO Consultation Notes, and Sign-off.

Each section must be completed in full. Incomplete DPIAs will be returned by the DPO for revision. Average completion time for a standard DPIA is 4-6 hours; complex DPIAs may require 2-3 weeks.

The Risk Assessment Matrix uses a 5x5 grid (Likelihood x Impact), with risk levels colour-coded: Green (acceptable), Amber (requires mitigation), Red (requires senior management approval), and Black (must not proceed without ICO consultation)."""),

    ("5. Roles and Responsibilities",
     """Project Owner: responsible for initiating the DPIA, providing accurate information about the processing, implementing approved mitigations, and maintaining the DPIA record throughout the project lifecycle.

Data Protection Officer: provides independent advice on the DPIA process, reviews completed assessments, escalates high-risk processing to the ICO where required, and maintains the central DPIA register.

Information Asset Owner: confirms the accuracy of data asset descriptions, approves the security measures proposed, and ensures ongoing compliance with DPIA conditions.

IT Security: advises on technical security measures, reviews proposed architectures for security adequacy, and validates that security controls are implemented as specified in the DPIA.

All completed DPIAs are stored in the central DPIA Register maintained by the DPO's office. The register is audited annually by Internal Audit."""),
]


# ──────────────────────────────────────────────────────────────────────
# Document 5 — Business Continuity Plan Summary  (~30 paragraphs)
# ──────────────────────────────────────────────────────────────────────

BCP_SECTIONS = [
    ("1. Purpose and Scope",
     """This Business Continuity Plan (BCP) outlines the procedures to maintain essential business functions during and after a disruptive event. Events covered include: natural disasters, cyber attacks, pandemic, loss of key personnel, supplier failure, and infrastructure failure.

The BCP covers all business units and functions. Critical business functions have been identified through a Business Impact Analysis (BIA) and are listed in Appendix A. Each critical function has a documented Maximum Tolerable Downtime (MTD) and recovery procedures.

The BCP is maintained by the Business Continuity Manager and reviewed by the Crisis Management Team quarterly. Full plan testing (tabletop exercise or live test) is conducted annually."""),

    ("2. Crisis Management Team",
     """The Crisis Management Team (CMT) consists of: Chief Executive (Chair), Chief Operating Officer, Chief Information Security Officer, Head of Communications, Head of HR, Head of Facilities, and the Business Continuity Manager (Secretary).

The CMT is activated when a disruptive event exceeds the capacity of normal operational management. Activation is triggered by the COO or, in their absence, the most senior available member of the CMT.

The CMT operates from the primary Crisis Management Room (Building A, Room G-01). If the primary location is unavailable, the secondary location (Building B, Room 2-15) is used. If neither is available, the CMT convenes virtually using the emergency Teams channel.

CMT decisions are documented in real-time by the Secretary using the Crisis Log template. Post-incident, the Crisis Log forms the basis of the post-incident review report."""),

    ("3. Communication Procedures",
     """Internal communication during a crisis is managed through the Mass Notification System (MNS). All employees must ensure their contact details (mobile phone, personal email) are up to date in the HRIS.

The MNS sends simultaneous notifications via SMS, email, and push notification. Test messages are sent quarterly to verify system functionality and contact data accuracy.

External communication during a crisis is managed exclusively by the Head of Communications. No other employee is authorised to make statements to media, regulators, or external stakeholders without explicit approval from the CMT.

Customer and partner notifications follow the Communication Protocol (BCP-003), which specifies templates, approval chains, and timing requirements for different incident categories.

Social media monitoring is intensified during crisis events. The Communications team monitors all major platforms and responds to queries/misinformation in accordance with the approved messaging framework."""),

    ("4. IT Disaster Recovery",
     """IT disaster recovery procedures are documented separately in the IT DR Plan (ITDR-001). The following provides a summary of key recovery objectives.

Recovery priorities are categorised as: Tier 1 — restore within 4 hours (email, authentication, VPN, core business applications), Tier 2 — restore within 24 hours (HRIS, financial systems, document management), Tier 3 — restore within 72 hours (development environments, training systems, analytics platforms).

All Tier 1 systems operate in active-active or active-passive high-availability configurations across two geographically separated data centres. Tier 2 and 3 systems are recovered from daily backups.

Backup strategy: Tier 1 systems — continuous replication with 15-minute RPO; Tier 2 systems — 4-hourly snapshots with 4-hour RPO; Tier 3 systems — daily backups with 24-hour RPO.

DR failover testing is conducted semi-annually. Each test involves a full failover of at least two Tier 1 systems to the secondary data centre, with success criteria including: successful failover within RTO, data integrity verification, and user acceptance testing.

Cyber-specific recovery procedures include: network isolation of affected segments, forensic preservation of evidence, clean restoration from known-good backups, and progressive reconnection with continuous monitoring."""),

    ("5. Business Recovery Procedures",
     """Each department maintains a Department Recovery Plan (DRP) that details how critical functions will be maintained during a disruption. DRPs must be reviewed and updated at least annually.

Work relocation options include: remote working (for disruptions affecting office premises), relocation to the backup office site (Building C, available at 24 hours notice with capacity for 150 staff), and buddy arrangements with named partner organisations.

Staff welfare during a crisis is coordinated by HR. This includes: regular communication updates, access to the Employee Assistance Programme (EAP), flexible working arrangements, and additional leave provisions where appropriate.

Supply chain continuity is managed by the Procurement team. Critical suppliers have been identified through the BIA and are subject to annual business continuity assessments. Alternative suppliers are pre-qualified for all single-source dependencies.

Financial provisions for crisis response, including emergency expenditure authorisation limits, are documented in the Finance appendix to this plan. The CFO has delegated authority for emergency spending up to 500,000 GBP without board approval."""),

    ("6. Plan Testing and Maintenance",
     """The BCP testing programme includes: quarterly tabletop exercises (scenario-based discussions), annual simulation exercises (partial activation of recovery procedures), and biennial full-scale tests (complete plan activation).

Testing results are documented in the Test Report template (BCP-005), including: scenario description, participants, actions taken, issues identified, and improvement recommendations.

Identified improvements are tracked in the BCP Improvement Register and assigned to responsible owners with target completion dates. Progress is reported to the CMT quarterly.

All employees must be aware of their roles and responsibilities under the BCP. Annual business continuity awareness is included in the mandatory security awareness training programme.

Department heads are responsible for maintaining their DRP, participating in testing exercises, and ensuring their teams are trained in recovery procedures. DRP compliance is included in the annual departmental audit."""),
]


# ──────────────────────────────────────────────────────────────────────
# Generate all documents
# ──────────────────────────────────────────────────────────────────────

def main():
    _build_pdf("Internal Policy Handbook",   HANDBOOK_SECTIONS,  RAW_DIR / "internal_policy_handbook_v2.pdf")
    _build_pdf("IT Security Addendum",       ADDENDUM_SECTIONS,  RAW_DIR / "it_security_addendum_2025.pdf")
    _build_pdf("HR Procedures Manual",       HR_SECTIONS,        RAW_DIR / "hr_procedures_manual.pdf")
    _build_pdf("Data Protection Impact Assessment Guide", DPIA_SECTIONS, RAW_DIR / "dpia_guide.pdf")
    _build_pdf("Business Continuity Plan Summary", BCP_SECTIONS, RAW_DIR / "business_continuity_plan.pdf")

    print(f"\n[+] All 5 documents generated in {RAW_DIR}/")


if __name__ == "__main__":
    main()
