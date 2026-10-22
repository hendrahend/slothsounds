"""Fine-tune the Sloth Sounds vibe translator on Tinker.

Teaches a small open-weight model (Qwen3.5-4B, LoRA) to turn lazy human
vibes into MusicGen-optimized prompts. Follows the Tinker SFT pattern:
ServiceClient -> LoRA training client -> forward_backward + optim_step
-> save weights -> sample.

Prereqs:
    pip install tinker tinker-cookbook
    export TINKER_API_KEY=...        # or: tinker auth login
    python scripts/build_vibe_dataset.py   # creates data/vibe_dataset.jsonl

If installing into the main venv (which pins torch 2.5.1+cu121 and
transformers 4.46.3 for audiocraft), avoid the dependency upgrade:

    pip install tinker tinker-cookbook --no-deps datasets==2.21.0

Run:
    python scripts/train_vibe_translator.py
    python scripts/train_vibe_translator.py --steps 40 --lr 0.0002
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root on path

BASE_MODEL = "Qwen/Qwen3.5-4B"
RENDERER_NAME = "qwen3_5"
LORA_RANK = 16
LEARNING_RATE = 2e-4
DEFAULT_STEPS = 30

TEST_VIBES = [
    "rainy sunday piano",
    "i am too tired to pick a playlist",
    "fireplace while it snows",
    "lofi for coding",
    "the audio equivalent of decaf",
]


def load_conversations(dataset_path: Path) -> list[list[dict]]:
    conversations = []
    with dataset_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                conversations.append(json.loads(line)["messages"])
    return conversations


async def main() -> None:
    parser = argparse.ArgumentParser(description="Fine-tune the vibe translator on Tinker")
    parser.add_argument("--data", default="data/vibe_dataset.jsonl")
    parser.add_argument("--model", default=BASE_MODEL)
    parser.add_argument("--steps", type=int, default=DEFAULT_STEPS)
    parser.add_argument("--lr", type=float, default=LEARNING_RATE)
    parser.add_argument("--rank", type=int, default=LORA_RANK)
    parser.add_argument("--checkpoint-name", default="slothsounds-vibe-translator")
    args = parser.parse_args()

    dataset_path = Path(args.data)
    if not dataset_path.exists():
        sys.exit(f"dataset not found: {dataset_path} — run scripts/build_vibe_dataset.py first")
    if not os.environ.get("TINKER_API_KEY"):
        sys.exit("TINKER_API_KEY not set — run `tinker auth login` or export the key")

    import numpy as np
    import tinker
    from tinker_cookbook.renderers import TrainOnWhat, get_renderer, get_text_content
    from tinker_cookbook.supervised.data import conversation_to_datum

    conversations = load_conversations(dataset_path)
    print(f"loaded {len(conversations)} training conversations from {dataset_path}")

    service_client = tinker.ServiceClient()
    training_client = await service_client.create_lora_training_client_async(
        base_model=args.model, rank=args.rank
    )
    tokenizer = training_client.get_tokenizer()
    renderer = get_renderer(RENDERER_NAME, tokenizer)

    training_data = [
        conversation_to_datum(
            conv, renderer, max_length=512, train_on_what=TrainOnWhat.LAST_ASSISTANT_MESSAGE
        )
        for conv in conversations
    ]
    print(f"built {len(training_data)} training examples")

    # Train: one pass over the dataset per step, cycling until --steps.
    for step in range(args.steps):
        batch = [training_data[(step + i) % len(training_data)] for i in range(8)]
        fwdbwd_future = await training_client.forward_backward_async(batch, "cross_entropy")
        optim_future = await training_client.optim_step_async(
            tinker.AdamParams(learning_rate=args.lr)
        )
        fwdbwd_result = await fwdbwd_future.result_async()
        await optim_future.result_async()
        logprobs = np.concatenate([out["logprobs"].tolist() for out in fwdbwd_result.loss_fn_outputs])
        weights = np.concatenate([d.loss_fn_inputs["weights"].tolist() for d in batch])
        loss = -np.dot(logprobs, weights) / weights.sum()
        print(f"step {step:3d}: loss = {loss:.4f}")

    # Save weights and sample to verify the model learned the format.
    save_result = await training_client.save_weights_async(name=args.checkpoint_name)
    print(f"checkpoint saved: {save_result.path}")
    sampling_client = await training_client.save_weights_and_get_sampling_client_async()

    stop = renderer.get_stop_sequences()
    params = tinker.SamplingParams(max_tokens=120, temperature=0.7, stop=stop)
    print("\n--- sampling the fine-tuned translator ---")
    for vibe in TEST_VIBES:
        messages = [
            {"role": "system", "content": conversations[0][0]["content"]},
            {"role": "user", "content": vibe},
        ]
        prompt = renderer.build_generation_prompt(messages)
        result = await sampling_client.sample_async(
            prompt=prompt, num_samples=1, sampling_params=params
        )
        response, _ = renderer.parse_response(result.sequences[0].tokens)
        answer = get_text_content(response)
        print(f"\nvibe   : {vibe}\nprompt : {answer}")


if __name__ == "__main__":
    asyncio.run(main())
