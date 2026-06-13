from __future__ import annotations

import uvicorn


def main() -> None:
    uvicorn.run("atext.api:app", host="0.0.0.0", port=8200)


if __name__ == "__main__":
    main()
