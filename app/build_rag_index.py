import sys
from app.rag_index import build_index

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m app.build_rag_index <PACK_ID>")
        print("Example: python -m app.build_rag_index KS3_Maths")
        raise SystemExit(1)

    pack_id = sys.argv[1]
    path = build_index(pack_id)
    print(f"✅ Built index: {path}")

if __name__ == "__main__":
    main()
