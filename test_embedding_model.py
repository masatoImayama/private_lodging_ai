from vertexai.language_models import TextEmbeddingModel
import vertexai

def find_working_model():
    vertexai.init(project="private-lodging-ai", location="us-central1")

    # 試すモデル名のリスト
    model_names = [
        "textembedding-gecko@003",
        "textembedding-gecko@002",
        "textembedding-gecko@latest",
        "textembedding-gecko",
        "text-gecko@003",
        "text-gecko@002",
    ]

    for model_name in model_names:
        print(f"Trying: {model_name}")
        try:
            model = TextEmbeddingModel.from_pretrained(model_name)
            print(f"SUCCESS: {model_name} is available")
            return model_name
        except Exception as e:
            print(f"Failed: {str(e)[:100]}")

    return None

if __name__ == "__main__":
    working_model = find_working_model()
    if working_model:
        print(f"\n使用可能なモデル: {working_model}")
    else:
        print("\n使用可能なモデルが見つかりませんでした")