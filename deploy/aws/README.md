# Deploy PolicyRAG on one AWS GPU instance (Option 1)

Runs the whole stack (Ollama + qwen2.5 7b/3b, FastAPI, Streamlit UI, Redis) with `docker compose` on a
single EC2 GPU instance. **Nothing is exposed to the internet:** the firewall allows only SSH from your
current IP, and you reach the app through an SSH tunnel at `http://localhost:8501`.

```
your PC ──ssh tunnel──► EC2 g6.xlarge (NVIDIA L4 24 GB)
                         └─ docker compose: ollama · ollama-pull · redis · api · ui
                            (all ports bound to 127.0.0.1 on the instance)
```

## Cost (us-east-1, on-demand; check the [EC2 pricing page](https://aws.amazon.com/ec2/pricing/on-demand/))

| item | approx. |
|---|---|
| g6.xlarge while **running** | ~$0.80 / hour |
| 100 GB gp3 disk (billed even when stopped) | ~$8 / month |
| left running 24/7 by mistake | **~$600 / month** |

A 2-hour demo costs about $2. Always `stop` when you're done.

## One-time setup

1. **AWS account + billing alarm.** In the console: *Billing → Budgets → Create budget → Monthly cost
   budget*, e.g. $20, with an email alert. Do this first.
2. **AWS CLI v2:** `winget install Amazon.AWSCLI`, then open a new terminal.
3. **Credentials:** create an IAM user (or use IAM Identity Center) with EC2 permissions, then run
   `aws configure` and enter the access key, secret, and region `us-east-1`.
4. **GPU quota.** New accounts usually have **0** vCPUs for GPU instances. Request 4:
   ```powershell
   aws service-quotas request-service-quota-increase --service-code ec2 --quota-code L-DB2E81BA --desired-value 4 --region us-east-1
   ```
   ("Running On-Demand G and VT instances"). Approval can take from minutes to a day. `launch` checks
   this and stops with this command if the quota is too low.

## Use

```powershell
cd policy-rag
.\deploy\aws\ec2.ps1 launch     # key pair + firewall + instance; prints the public IP
.\deploy\aws\ec2.ps1 logs       # watch first-boot setup (~10-20 min: drivers check, models, image build)
.\deploy\aws\ec2.ps1 status     # "ready" when done
.\deploy\aws\ec2.ps1 tunnel     # keep open, then browse http://localhost:8501 (API: :8000/docs)
.\deploy\aws\ec2.ps1 stop       # GPU billing ends; disk kept
.\deploy\aws\ec2.ps1 start      # resume later (~2 min; firewall re-pinned to your current IP)
.\deploy\aws\ec2.ps1 destroy    # delete instance, disk, firewall and key pair
```

Options: `-Region eu-west-1`, `-InstanceType g5.xlarge`, `-VolumeGb 150`.

## What the scripts do

**`ec2.ps1 launch`** (runs on your PC):
- checks the AWS CLI, your account and the GPU quota
- creates an ed25519 key pair and saves the private key to `~\.ssh\policyrag-key.pem`, readable only
  by you
- creates security group `policyrag-ssh` allowing **TCP 22 from your IP /32 only**
- finds the newest AWS *Deep Learning Base OSS Nvidia Driver GPU AMI (Ubuntu)*, which has the NVIDIA
  driver preinstalled
- launches with an encrypted 100 GB gp3 disk, IMDSv2 required, and `bootstrap.sh` as user data

**`bootstrap.sh`** (runs on the instance at first boot, as root; log in `/var/log/policyrag-bootstrap.log`):
1. verifies the GPU (`nvidia-smi`)
2. installs Docker + the compose plugin and the NVIDIA Container Toolkit if missing, then proves a
   container can see the GPU
3. clones this repo to `/opt/policy-rag`
4. `docker compose build && up -d`: pulls qwen2.5:7b + 3b (~6.6 GB), builds the API image with the bge
   models baked in, and builds the FAISS index
5. waits for `/health` to report `ok`, then writes `ready` to `/var/log/policyrag-status`

Services restart automatically after `stop` → `start` (`restart: unless-stopped`).

## Troubleshooting

| symptom | fix |
|---|---|
| `GPU quota too low` | request the increase above and wait for approval |
| `InsufficientInstanceCapacity` | try another AZ/region (`-Region us-west-2`) or `-InstanceType g5.xlarge` |
| `ssh: connection timed out` | your IP changed; run `stop` then `start` (re-pins the firewall), or relaunch |
| status stuck at `building` | `logs`; the first build downloads several GB, so allow 20 min |
| status `failed: ...` | `logs` shows the failing step; fix it, then on the instance `sudo bash /opt/policy-rag/deploy/aws/bootstrap.sh` |
| UI loads but answers are slow | normal for the first query (model warm-up). The API's reranker runs on CPU in this image; the LLM uses the GPU |

## Limits of this setup (not production)

- **No real authentication.** Anyone with tunnel access can pick the `staff` role in the UI. That is
  acceptable only because the instance is reachable just by you. Production needs Cognito/JWT
  (see [`docs/PROJECT_GUIDE.md`](../../docs/PROJECT_GUIDE.md) §10).
- Single instance: no redundancy, and the review queue is SQLite inside the container volume.
- **Verification status:** `ec2.ps1` was parse-checked and dry-run (it fails cleanly without the AWS CLI),
  and the compose file was validated. The scripts **have not yet been run against a live AWS account**.
  The first real launch is the real test, so watch `logs` on the first run.
