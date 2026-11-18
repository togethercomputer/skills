# Live GPU Cluster Inventory and Pricing

Use this path when the user asks what is available, what is cheapest, or for a
command they can inspect without creating a cluster.

## Contents

- [Authoritative surfaces](#authoritative-surfaces)
- [Read-only inventory](#read-only-inventory)
- [Choosing the cheapest live option](#choosing-the-cheapest-live-option)
- [A one-hour on-demand plan is create, then delete](#a-one-hour-on-demand-plan-is-create-then-delete)

## Authoritative surfaces

The two required surfaces answer different questions:

1. Query `GET https://api.together.ai/v1/compute/regions` or run
   `tg clusters list-regions --json` for the live region inventory,
   supported instance types, and driver versions. Each driver version has an
   `id`, a `cuda_version`, an `nvidia_driver_version`, and an `os`.
2. Open the [GPU Cluster pricing table](https://www.together.ai/pricing#gpu-clusters)
   for current on-demand and reserved rates. Prices are per GPU per hour.

For billing rules (how reserved, on-demand, and storage charges accrue, and the
credits a create request needs), see
[GPU clusters pricing and billing](https://docs.together.ai/docs/gpu-clusters-billing).

The regions response does **not** include pricing or prove that capacity is in
stock. Do not infer price from GPU generation, response order, or a static
instance-type list. A create request can still return `409 Out of stock`.

## Read-only inventory

```shell
tg clusters list-regions --json
```

Or use REST:

```shell
curl --fail-with-body --silent --show-error \
  "https://api.together.ai/v1/compute/regions" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  | jq -r '.regions[] | [.name, (.supported_instance_types | join(","))] | @tsv'
```

When reporting current availability, execute one of these read-only lookups and
list every region and its supported instance types. In the proposed create
command, use one driver version from the selected region: its `id` as
`--nvidia-version-id`, or its `nvidia_driver_version` and `cuda_version` as
`--nvidia-driver-version` and `--cuda-version`.

## Choosing the cheapest live option

1. Collect the unique instance types from the live regions response.
2. Match those types to the hardware rows in the official pricing table.
3. Compare numeric **on-demand** rates only. Treat an em dash or “contact us”
   as no public numeric rate; never invent a number.
4. Report the selected per-GPU-hour rate and the total hourly cluster cost.

Every cluster needs at least 8 GPUs, in multiples of 8. The minimum hourly
compute estimate is therefore:

```text
8 × selected on-demand price per GPU-hour
```

Every cluster also needs a shared volume, which bills separately per GiB per
month. Say so when you quote a total.

## A one-hour on-demand plan is create, then delete

`ON_DEMAND` has no duration setting. `--duration-days` applies to reserved
capacity and must not be added to an on-demand command. “Run for one hour” means
create the cluster, let it run for the intended period, then delete it.

The API rejects a create request that has no shared volume, so the command
either creates one with the cluster (`--shared-volume-name` with
`--shared-volume-size-tib`, CLI 3.2.0 and later) or attaches an existing one
(`--volume <VOLUME_ID>`).

If the user asks only to show the command, fill the placeholders below from the
live inventory and print the commands without executing them:

```shell
tg clusters create \
  --name one-hour-gpu-cluster \
  --num-gpus 8 \
  --gpu-type <CHEAPEST_LIVE_GPU_TYPE> \
  --region <LIVE_REGION_SUPPORTING_THAT_TYPE> \
  --nvidia-version-id <LIVE_NVIDIA_VERSION_ID> \
  --billing-type ON_DEMAND \
  --cluster-type KUBERNETES \
  --shared-volume-name one-hour-gpu-cluster-data \
  --shared-volume-size-tib 1 \
  --non-interactive \
  --json

# After approximately one hour, delete the ID returned by create:
tg clusters delete <CLUSTER_ID> --non-interactive

# Deleting the cluster keeps the volume, which keeps billing. Find it and delete it:
tg clusters storage list
tg clusters storage delete <VOLUME_ID> --non-interactive
```

`<LIVE_NVIDIA_VERSION_ID>` is the `id` of a driver version listed for that
region. `--nvidia-driver-version` with `--cuda-version` from the same entry
works in its place.

There is no cluster-create dry-run flag. A “dry run” in this context means
rendering a complete command with live values and not invoking it.
