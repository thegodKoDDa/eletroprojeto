import os
import shutil
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path

import test_continuity
from continuity import verify
from external_backup import encrypt_checkpoint


@unittest.skipUnless(shutil.which("gpg"), "GPG não disponível nesta plataforma")
class EncryptedBackupTests(unittest.TestCase):
    def test_encryption_roundtrip_preserves_verified_checkpoint(self):
        fixture = test_continuity.ContinuityTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        import continuity

        if shutil.which("git"):
            for args in [
                ("init",),
                ("add", "AGENTS.md"),
                (
                    "-c",
                    "user.name=QA",
                    "-c",
                    "user.email=qa@example.invalid",
                    "commit",
                    "-m",
                    "QA baseline",
                ),
            ]:
                subprocess.run(
                    ["git", "-C", str(fixture.root), *args], check=True, capture_output=True
                )

        result = continuity.checkpoint(fixture.root)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            home, target = root / "keys", root / "external"
            home.mkdir(mode=0o700)
            target.mkdir()
            command = [
                "gpg",
                "--homedir",
                str(home),
                "--batch",
                "--pinentry-mode",
                "loopback",
                "--passphrase",
                "",
            ]
            subprocess.run(
                [
                    *command,
                    "--quick-generate-key",
                    "EletroProjeto QA <qa@example.invalid>",
                    "rsa2048",
                    "encr",
                    "0",
                ],
                check=True,
                capture_output=True,
            )
            listing = subprocess.run(
                [*command, "--with-colons", "--list-keys"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout
            fingerprint = next(
                line.split(":")[9] for line in listing.splitlines() if line.startswith("fpr:")
            )
            encrypted = encrypt_checkpoint(
                Path(result["checkpoint"]), target, fingerprint, homedir=home
            )
            self.assertTrue(encrypted["transfer_verified"])
            self.assertFalse(encrypted["recipient_restore_verified"])
            with self.assertRaises(ValueError):
                encrypt_checkpoint(Path(result["checkpoint"]), target, fingerprint, homedir=home)
            restored_tar = root / "restored.tar"
            subprocess.run(
                [*command, "--output", str(restored_tar), "--decrypt", encrypted["path"]],
                check=True,
                capture_output=True,
            )
            with tarfile.open(restored_tar) as archive:
                archive.extractall(root / "restore", filter="data")
            restored = root / "restore" / Path(result["checkpoint"]).name
            self.assertTrue(verify(restored)["verified"])
            if os.name != "nt":
                self.assertEqual(Path(encrypted["path"]).stat().st_mode & 0o777, 0o600)
