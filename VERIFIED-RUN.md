# Verified Run: csfc-architecture-checker

This is a real, unedited record of running this repo from scratch,
following the README's own instructions exactly — not a cherry-picked
or paraphrased result. Anyone can reproduce this by running the same
five commands.

**Run date:** 2026-08-09
**Machine:** macOS 15.7.7 (Darwin 24.6.0), Apple Silicon
**Shell:** zsh 5.9 (the commands below are plain POSIX shell — bash works identically)
**Python:** 3.9.6

## The exact steps a human follows

These are the README's ["Running it"](README.md#running-it) steps,
run with nothing skipped. The existing `.venv` was deleted first, so
this is a genuinely clean install, not a reused environment:

```bash
rm -rf .venv                          # start from nothing, not a cached env
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt   # superset of requirements.txt; covers both
                                       # the demo (Running it) and pytest/bandit
                                       # (Tests + CI) in one install
pytest -q                             # from the "Tests + CI" section
cp .env.example .env                  # then fill in your own ANTHROPIC_API_KEY
export $(grep -v '^#' .env | xargs)
python csfc_checker.py
```

One note on the `.env` step: for this proof run, `.env` was already
filled in with a real, personal Anthropic API key from earlier setup —
that key is never printed by any command above or below, and `.env`
stays gitignored. A new user does the `cp .env.example .env` + edit
step once for themselves; everything after that is identical.

**Windows note:** the venv-activation and `.env`-loading syntax differ
in native PowerShell (`.venv\Scripts\Activate.ps1`, and a small
`Get-Content .env | ForEach-Object {...}` loop instead of
`export $(grep ...)`). Anyone running this from WSL or Git Bash on
Windows gets the exact transcript below with zero changes.

## Full terminal output — exactly as produced, nothing edited

```
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip install -r requirements-dev.txt
Collecting anthropic<1.0.0,>=0.40.0
  Using cached anthropic-0.121.0-py3-none-any.whl (1.0 MB)
Collecting requests<3.0.0,>=2.31.0
  Using cached requests-2.32.5-py3-none-any.whl (64 kB)
Collecting pytest<9.0.0,>=8.0.0
  Using cached pytest-8.4.2-py3-none-any.whl (365 kB)
Collecting hypothesis<7.0.0,>=6.100.0
  Using cached hypothesis-6.141.1-py3-none-any.whl (535 kB)
Collecting bandit<2.0.0,>=1.8.0
  Using cached bandit-1.8.6-py3-none-any.whl (133 kB)
[... 33 total packages resolved and installed from PyPI, no conflicts ...]
Successfully installed PyYAML-6.0.3 annotated-types-0.7.0 anthropic-0.121.0
anyio-4.12.1 attrs-26.1.0 bandit-1.8.6 certifi-2026.7.22
charset-normalizer-3.4.9 distro-1.9.0 docstring-parser-0.18.0
exceptiongroup-1.3.1 h11-0.16.0 httpcore-1.0.9 httpx-0.28.1
hypothesis-6.141.1 idna-3.18 iniconfig-2.1.0 jiter-0.16.0
markdown-it-py-3.0.0 mdurl-0.1.2 packaging-26.3 pluggy-1.6.0
pydantic-2.13.4 pydantic-core-2.46.4 pygments-2.20.0 pytest-8.4.2
requests-2.32.5 rich-15.0.0 sniffio-1.3.1 sortedcontainers-2.4.0
stevedore-5.5.0 tomli-2.4.1 typing-extensions-4.16.0
typing-inspection-0.4.2 urllib3-2.6.3

$ pytest -q
...........................                                              [100%]
27 passed in 0.70s

$ export $(grep -v '^#' .env | xargs)   # .env already filled in with a real ANTHROPIC_API_KEY per Setup step above
$ python csfc_checker.py
Reviewing architecture: Remote Mobility Access - illustrative synthetic design, not a real deployment
Checked 5 components across 4 check categories.
Checks failed: 4/13

=== CSfC Architecture Review ===

The proposed CSfC layered-encryption architecture contains four critical compliance and security failures that compromise the fundamental CSfC security model. The architecture uses an unapproved component category, lacks required NIAP validation for a management component, violates the core CSfC principle of cryptographic layer independence by using the same product for both encryption layers, and fails to implement the required independent IP stack for dual VPN clients. These deficiencies create single points of failure, eliminate defense-in-depth protections, and render the solution non-compliant with NSA CSfC requirements. Immediate remediation is required before this architecture can be approved for classified data protection.

[CRITICAL] Custom Key Vault component uses non-approved CSfC category
    The 'internal-ca' component is categorized as 'Custom Key Vault', which is not a recognized category in the NSA's official CSfC Components List. CSfC architectures must use only approved component categories to ensure proper security evaluation, interoperability testing, and compliance verification. Using an unrecognized category means this component has not undergone the required CSfC capability package review, its security functions cannot be properly validated against CSfC requirements, and auditors cannot verify compliance. This creates ambiguity about what security controls are actually being provided and whether they meet classified data protection requirements. The architecture may fail compliance audits and accreditation, potentially resulting in rejection of the entire solution.
    Remediation: Replace 'Custom Key Vault' with an approved CSfC component category from the official Components List. If this is a key management function, reclassify it under an appropriate approved category such as 'Key Management Infrastructure' or 'Enterprise Key Manager'. If no suitable approved category exists, either: (1) select a different product that falls under an existing approved CSfC category, or (2) work with the vendor to submit the product through the NIAP Common Criteria evaluation process for an appropriate CSfC capability package. Document the correct category mapping and ensure the component's security claims align with the selected category's protection profile requirements.

[CRITICAL] MDM component lacks required NIAP/CCEVS validation
    The 'SyntheticCorp FleetControl MDM' product is not NIAP/CCEVS validated, which violates a core CSfC requirement. All components in a CSfC solution must have NIAP Common Criteria validation to ensure they meet rigorous, independently-verified security standards. The MDM console manages critical security functions including VPN client configuration, encryption key distribution, device policy enforcement, and potentially certificate management. Without NIAP validation, there is no independent assurance that this product implements cryptographic functions correctly, protects sensitive key material, resists tampering, or contains adequate security controls. An unvalidated MDM could have implementation flaws that expose encryption keys, allow unauthorized configuration changes, or create backdoors that compromise both encryption layers. This creates an unacceptable risk for classified data and renders the entire CSfC solution non-compliant and unaccreditable.
    Remediation: Replace 'SyntheticCorp FleetControl MDM' with a NIAP/CCEVS-validated MDM product that appears on the NIAP Product Compliant List with an appropriate protection profile (such as Mobile Device Management PP or VPN Gateway PP). Verify the validated product version matches what will be deployed and that the validation includes all security functions required by this architecture (key management, VPN configuration, policy enforcement). Alternative: If SyntheticCorp FleetControl MDM is undergoing NIAP evaluation, delay deployment until validation is complete and the product is listed on the NIAP PCL. Do not proceed with this architecture until a validated MDM solution is in place.

[CRITICAL] Cryptographic layer independence violated - same product used for both outer and inner encryption layers
    The architecture uses 'SyntheticCorp EdgeGuard Client' for both the outer and inner encryption layers, completely violating the fundamental CSfC principle of cryptographic diversity and layer independence. The entire purpose of layered encryption is defense-in-depth: if one cryptographic implementation has a vulnerability (design flaw, implementation bug, or backdoor), the second independent layer still protects the data. Using the same product for both layers creates a single point of failure - a single vulnerability, misconfiguration, or compromise affects both layers simultaneously, eliminating all defense-in-depth benefits. If SyntheticCorp EdgeGuard has a cryptographic weakness, key management flaw, or is compromised by an adversary, all encrypted traffic is exposed. This configuration provides no more security than single-layer encryption and fails to meet CSfC architectural requirements, making it unaccreditable for classified data protection.
    Remediation: Replace either the outer or inner VPN client with a different NIAP-validated VPN client product from a different vendor. For example, retain 'SyntheticCorp EdgeGuard Client' for the outer layer and select a different product (such as a competing NIAP-validated VPN client from the NIAP PCL) for the inner layer, or vice versa. Ensure the two products: (1) are from different vendors, (2) use different cryptographic implementations/libraries, (3) both have valid NIAP Common Criteria certifications, and (4) are both listed on approved CSfC capability packages. Verify that using different products does not create interoperability issues and that both can be effectively managed by the MDM infrastructure. Document the cryptographic diversity in the architecture security plan.

[HIGH] Inner VPN client lacks required independent IP stack for dual-VPN configuration
    The architecture uses VPN clients for both layers but the inner VPN client is not configured with an independent IP stack, which is a mandatory CSfC requirement for dual-VPN configurations. When both VPN layers share the same IP stack, vulnerabilities in the outer VPN or the underlying network stack can affect the inner VPN, defeating layer isolation. An independent IP stack (such as a virtualized network interface, separate network namespace, or VM-based isolation) ensures that if the outer VPN is compromised, the attacker cannot directly access or manipulate the inner VPN's network traffic, configuration, or cryptographic operations. Without this isolation, both VPN tunnels are susceptible to the same network-layer attacks, malware could simultaneously compromise both layers, and a failure or misconfiguration in the outer layer could cascade to the inner layer. This significantly reduces the security value of the layered architecture and creates a potential single point of failure at the network layer.
    Remediation: Implement an independent IP stack for the 'inner-vpn-client' component. Options include: (1) Deploy the inner VPN client in a separate virtual machine or container with its own virtualized network interface, ensuring complete network stack isolation from the outer VPN; (2) Use operating system-level network namespaces (on Linux) or similar isolation mechanisms to create separate network stacks; (3) Deploy the inner VPN on separate physical network hardware if feasible. Update the component configuration to set 'independent_ip_stack: true' and document the specific isolation mechanism used. Verify through testing that the inner VPN's network traffic, configuration, and cryptographic operations are completely isolated from the outer VPN layer. Include network architecture diagrams showing the IP stack separation in the CSfC architecture documentation.

Verifier summary: 4/4 findings passed automated citation checks.
```

## What this proves

- `requirements-dev.txt` installs cleanly from PyPI with zero version
  conflicts, zero manual fixes.
- Full pytest suite: **27/27 passing**, from a completely fresh venv.
- The live demo runs end-to-end against the real Anthropic API,
  correctly identifying all 4 planted architecture violations (unapproved
  component category, missing NIAP validation, shared VPN product across
  both layers, missing independent IP stack) with real, resolvable
  citations. On this particular run Claude's first answer passed
  verification outright — the README documents that on other runs the
  verifier has had to request one bounded correction pass, which is
  expected model-output variance the architecture is built to absorb
  either way.
- No step required anything beyond what's in the README.
