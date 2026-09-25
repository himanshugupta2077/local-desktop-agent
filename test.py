from transformers import AutoProcessor, AutoModelForCausalLM

processor = AutoProcessor.from_pretrained(
    "microsoft/Florence-2-large-ft",
    trust_remote_code=True
)

model = AutoModelForCausalLM.from_pretrained(
    "microsoft/Florence-2-large-ft",
    trust_remote_code=True
)

processor.save_pretrained(
    "weights/icon_caption_florence_large"
)

model.save_pretrained(
    "weights/icon_caption_florence_large"
)

