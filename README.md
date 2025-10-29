# Contest submissions analyzer

This CLI watches Sherlock and Code4rena contests, giving you an at-a-glance breakdown of judging progress, expected rewards, and (optionally) Telegram alerts when something changes.

## Setup

1. Rename `.env.example` to `.env`.
2. Populate the environment variables:

   - **Required for Sherlock**
     - `SESSION_SHERLOCK`: the `session` cookie from https://audits.sherlock.xyz.
   - **Required for Code4rena**
   - `CODE4_USER`: your Code4rena handle (used for authenticating the API).
   - `CODE4_PASS`: the password for the Code4rena account referenced by `CODE4_USER`.

   - **Optional**
     - `BOT_TOKEN` / `CHAT_ID`: Telegram bot credentials for notifications.
     - `SENTRY_DSN`: enable crash reporting through Sentry.

3. Install locally: `pipx install -e .`

### Extracting the session cookies

**Sherlock**

- Log in, open the browser dev tools, inspect any request, and copy the `session` cookie value into `SESSION_SHERLOCK`.

**Code4rena**

- Set `CODE4_USER` to your Code4rena handle and `CODE4_PASS` to the corresponding password (used to acquire an API session automatically). These variables must be present in your environment (or `.env`) before running the Code4rena analyzer.

## Usage

Both analyzers accept `-t/--timeout` to keep polling (in seconds). When omitted they run once.

## Project layout

```
submission_analyzer/
└── platforms/
    ├── sherlock/    # Sherlock CLI, API client, and models
    └── code4rena/   # Code4rena CLI, connector, and models
```

### Sherlock

```
sherlock-analyzer [-h] [-e] [-c] [-t TIMEOUT] contestId
```

- `-e / --escalations`: show escalations summary.
- `-c / --comments`: fetch and print Lead Judge comments (slow; one request per issue).

Example output (`sherlock-analyzer -e 964`):

```
27/08/2025 - 13:00:08
=== Contest 964 — Breakdown   ===
Total issues: 710 - valid issues: 232 - invalid issues: 478 - your total issues: 6 - your valid issues: 5 - your invalid issues: 1
Your total expected reward: 2081.18
Escalations: 35 escalated | 35 resolved | 0 pending

#     Title                                                                     Sev    Dup     Points       Reward  Mine   Esc   Res
--------------------------------------------------------------------------------------------------------------------------------------------
491   Redeems through RedeemQueue avoid paying management and performance f…    High     2     1.3500      3047.46     N     Y     Y
617   Targeted-lockup bypass: freshly minted shares can be transferred imme…    Medium   0     1.0000      2257.38     N     N     N
207   Incorrect performance fee calculation in `FeeManager`                     High     4     0.6561      1481.07     Y     Y     Y
739   Stuck `stETH` rewards in queue contracts                                  Medium   2     0.2700       609.49     N     Y     Y
167   Protocol Fee Multiple Accrual in Oracle.submitReports                     High     8     0.2391       539.85     Y     N     N
141   stETH edge case in transfer rounding can cause denial of service for …    Medium   3     0.1823       411.41     N     Y     Y
161   Protocol Fee Exponential Compounding in ShareModule.handleReport          Medium   3     0.1823       411.41     N     N     N
688   DoS in Redemption Due to Unchecked Asset Support in Subvaults             Medium   5     0.0984       222.16     N     Y     Y
711   Malicious Users Can Perpetually Lock `feeRecipient` Shares via Target…    Medium   8     0.0478       107.97     N     Y     Y
147   Unable to withdraw native tokens because vault and redeem hooks do no…    High    17     0.0463       104.57     N     Y     Y
140   ETH redemptions via `SignatureRedeemQueue` are broken due to missing …    Medium   9     0.0387        87.46     N     Y     Y
65    RedeemQueue Accounting Mismatch Between Batch Creation and Claim Elig…    High    21     0.0249        56.14     Y     Y     Y
246   cancelDepositRequest() always reverts due to modifying FenwickTree wi…    Medium  28     0.0018         4.07     Y     Y     Y
13    `Consensus`.`checkSignatures` doesn't check duplication of signers        High    45     0.0009         2.14     N     N     N
26    Flawed Logic in `ShareManager` Inverts Transfer Whitelist Behavior        Medium  62     0.0000         0.05     Y     N     N
--------------------------------------------------------------------------------------------------------------------------------------------

=== Invalid issues (escalated) ===

#     Title                                                                     Dup  Mine   Esc   Res
--------------------------------------------------------------------------------------------------------------------------------------------
11    Users whitelisted on chain are unable to deposit if a merkle tree is als…   0     N     Y     Y
132   Early return in `DepositQueue._handleReport` function causes unclaimable…   0     N     Y     Y
144   Receiver blacklist check missing in transfer path of `ShareManager.updat…   0     N     Y     Y
174   Oracle report processing will cause complete failure for all assets when…   0     N     Y     Y
190   Asset removal creates permanently orphaned funds and unprocessable reque…   0     N     Y     Y
203   Inconsistent price usage will cause inaccurate balance tracking in `subV…   0     N     Y     Y
210   Inconsistent share decimals calculation breaks protocol accounting for m…   0     N     Y     Y
315   `canDeposit` Flag can Blocks Transfer and Burn of Already Minted Shares     0     N     Y     Y
330   Incorrect Flag Usage Bypasses On-Chain Deposit & Transfer Restrictions      0     N     Y     Y
377   `setFees` does not mint fees first.                                         4     N     Y     Y
482   Depositors are unable to claim shares after DepositQueue is removed         0     N     Y     Y
485   Signature queues do not charge management and performance fees before ex…   0     N     Y     Y
520   Attacker can temporarily delay an eoa/contract from being able to initia…   0     N     Y     Y
552   Pausing mint in sharemanager effectively pauses the entire system           0     N     Y     Y
559   No fees paid on signature queues                                            0     N     Y     Y
565   Risk manager is not updated when protocol and performance fees are minte…   0     N     Y     Y
594   Error in how RiskManager means there will allows be discrepancies betwee…   0     N     Y     Y
605   wrong use of index which lead for the function to not work properly         0     N     Y     Y
722   Pausing minting disables core protocol functionality                        0     N     Y     Y
```

### Code4rena

```
code4rena-analyzer [-h] [-p PRIZE_POOL] [-u USER] [-t TIMEOUT]
                   [--include-invalid] [--max-title WIDTH]
                   [--highlight-mine] contestId
```

- `-p / --prize-pool`: high/medium prize pool allocation in USD (if omitted, rewards stay at $0 unless `CODE4RENA_PRIZE_POOL` is set).
- `-u / --user`: Code4rena handle (defaults to `CODE4RENA_HANDLE`).
- `--include-invalid`: display invalid / non-winning findings in the table.
- `--max-title`: adjust title truncation width.
- `--highlight-mine`: color rows that match your handle when the terminal supports ANSI colors.

Both analyzers reuse the same Telegram bot credentials and Sentry DSN. Notifications are sent only when the underlying data changes, keeping noise low while still updating you when judging progresses.
