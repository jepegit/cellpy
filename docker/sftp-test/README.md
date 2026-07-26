# SFTP test server (Docker)

Provides a local `atmoz/sftp` instance for real `OtherPath` property tests
(`tests/test_otherpaths_sftp.py`).

| Setting | Value |
| --- | --- |
| Host / port | `127.0.0.1:2223` |
| User / password | `cellpy` / `cellpy` |
| Fixture files | `/testdata/...` (chroot view of `./data`) |

```bash
# from repo root
docker compose -f docker/sftp-test/compose.yml up -d --wait
uv run pytest tests/test_otherpaths_sftp.py -m onlylocal
docker compose -f docker/sftp-test/compose.yml down -v
```

The pytest session fixture starts/stops compose automatically when Docker is
available; these tests are marked `onlylocal` and are deselected by the default
`addopts` marker filter. After start it creates a directory symlink
`testdata/project_link` → `nested` (volume is mounted read-write) so
`OtherPath.rglob` symlink-following can be exercised (#688).
