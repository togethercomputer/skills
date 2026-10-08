# Live GPU Cluster Inventory and Pricing

Use this path when the user asks what is available, what is cheapest, or for a
command they can inspect without creating a cluster.

## Authoritative surfaces

The two required surfaces answer different questions:

1. Query `GET https://api.together.ai/v1/compute/regions` or run
   `tg beta clusters list-regions --json` for the live region inventory,
   supported instance types, and compatible CUDA/driver pairs.
2. Open the [GPU Cluster pricing table](https://www.together.ai/pricing#gpu-clusters)
   for current on-demand and reserved rates. Prices are per GPU per hour.

The regions response does **not** include pricing or prove that capacity is in
stock. Do not infer price from GPU generation, response order, or a static
instance-type list. A create request can still return `409 Out of stock`.

## Read-only inventory

```shell
tg beta clusters list-regions --json
```

Or use REST:

```shell
curl --fail-with-body --silent --show-error \
  "https://api.together.ai/v1/compute/regions" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  | jq -r '.regions[] | [.name, (.supported_instance_types | join(","))] | @tsv'
```

When reporting current availability, execute one of these read-only lookups and
list every region and its supported instance types. Use one compatible
`cuda_version` / `nvidia_driver_version` pair from the selected region in the
proposed create command.

## Choosing the cheapest live option

1. Collect the unique instance types from the live regions response.
2. Match those types to the hardware rows in the official pricing table.
3. Compare numeric **on-demand** rates only. Treat an em dash or “contact us”
   as no public numeric rate; never invent a number.
4. Report the selected per-GPU-hour rate and the total hourly cluster cost.

GPU clusters require `num_gpus` to be a multiple of 8, so the smallest cluster
uses 8 GPUs. The minimum hourly estimate is therefore:

```text
8 × selected on-demand price per GPU-hour
```

## A one-hour on-demand plan is create, then delete

`ON_DEMAND` has no duration setting. `--duration-days` applies to reserved
capacity and must not be added to an on-demand command. “Run for one hour” means
create the cluster, let it run for the intended period, then delete it.

If the user asks only to show the command, fill the placeholders below from the
live inventory and print the commands without executing them:

```shell
tg beta clusters create \
  --name one-hour-gpu-cluster \
  --num-gpus 8 \
  --gpu-type <CHEAPEST_LIVE_GPU_TYPE> \
  --region <LIVE_REGION_SUPPORTING_THAT_TYPE> \
  --nvidia-driver-version <LIVE_DRIVER_VERSION> \
  --cuda-version <LIVE_CUDA_VERSION> \
  --billing-type ON_DEMAND \
  --cluster-type KUBERNETES \
  --non-interactive \
  --json

# After approximately one hour, delete the ID returned by create:
tg beta clusters delete <CLUSTER_ID> --non-interactive
```

There is no cluster-create dry-run flag. A “dry run” in this context means
rendering a complete command with live values and not invoking it.
