import os
import pytest
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs

@pytest.mark.slow
def test_build_deb_process():
    """
    Tests the build-deb.sh script inside an Ubuntu 24.04 container.
    This ensures the build process works in a clean environment.
    """
    # Get the absolute path to the project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    # Define the container
    with DockerContainer("ubuntu:24.04") as container:
        # Mount the project directory
        container.with_volume_mapping(project_root, "/app")
        
        # Keep the container running
        container.with_command("tail -f /dev/null")
        container.start()
        
        # Helper to run commands and assert success
        def run_command(cmd):
            result = container.exec(cmd)
            # exec returns (exit_code, output_bytes) or similar depending on library version
            # The python testcontainers exec returns ExecResult(exit_code, output, stderr)
            assert result.exit_code == 0, f"Command failed: {cmd}\nOutput: {result.output}\nStderr: {result.stderr}"
            return result.output.decode('utf-8')

        # 1. Update apt and install dependencies
        print("Installing build dependencies...")
        run_command("apt-get update")
        run_command("apt-get install -y build-essential libssl-dev pkg-config gettext cargo cmake clang")

        # 2. Run the build script
        print("Running build-deb.sh...")
        # We run inside /app
        run_command("bash -c 'cd /app && ./build-deb.sh'")

        # 3. Verify the .deb file was created
        print("Verifying .deb creation...")
        ls_output = run_command("ls /app/build/*.deb")
        assert "amazon-efs-utils" in ls_output
        deb_file = ls_output.strip().split('\n')[0]
        print(f"Found deb file: {deb_file}")

        # 4. Try to install the .deb
        print("Installing the generated .deb...")
        run_command(f"apt-get install -y {deb_file}")

        # 5. Verify installation
        print("Verifying installation...")
        version_output = run_command("mount.efs --version")
        print(f"Installed version: {version_output.strip()}")
        assert "mount.efs" in version_output
