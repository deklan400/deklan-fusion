"""
SSH Client wrapper untuk komunikasi dengan VPS menggunakan paramiko.
Mendukung execute command dan upload file.
"""
import paramiko
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class SSHClient:
    """Wrapper untuk SSH operations menggunakan paramiko."""
    
    @staticmethod
    def execute(host: str, username: str, password: str, command: str, timeout: int = 30) -> Tuple[bool, str]:
        """
        Execute command via SSH.
        
        Args:
            host: IP address atau hostname
            username: SSH username
            password: SSH password
            command: Command yang akan dijalankan
            timeout: Timeout dalam detik
            
        Returns:
            Tuple (success: bool, output: str)
        """
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(host, username=username, password=password, timeout=timeout)
            
            stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
            output = stdout.read().decode('utf-8', errors='ignore')
            error = stderr.read().decode('utf-8', errors='ignore')
            
            client.close()
            
            if error and not output:
                return False, error
            return True, output
            
        except paramiko.AuthenticationException:
            logger.error(f"SSH Authentication failed for {host}")
            return False, "❌ Authentication failed"
        except paramiko.SSHException as e:
            logger.error(f"SSH Error for {host}: {str(e)}")
            return False, f"❌ SSH Error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error for {host}: {str(e)}")
            return False, f"❌ Error: {str(e)}"
    
    @staticmethod
    def upload_file(host: str, username: str, password: str, 
                   local_path: str, remote_path: str, timeout: int = 30) -> Tuple[bool, str]:
        """
        Upload file ke VPS via SFTP.
        
        Args:
            host: IP address atau hostname
            username: SSH username
            password: SSH password
            local_path: Path file lokal
            remote_path: Path tujuan di remote
            timeout: Timeout dalam detik
            
        Returns:
            Tuple (success: bool, message: str)
        """
        try:
            transport = paramiko.Transport((host, 22))
            transport.connect(username=username, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)
            
            # Ensure remote directory exists
            remote_dir = '/'.join(remote_path.split('/')[:-1])
            try:
                sftp.mkdir(remote_dir)
            except:
                pass  # Directory might already exist
            
            sftp.put(local_path, remote_path)
            sftp.close()
            transport.close()
            
            return True, f"✅ File uploaded to {host}:{remote_path}"
            
        except Exception as e:
            logger.error(f"SFTP upload error for {host}: {str(e)}")
            return False, f"❌ Upload failed: {str(e)}"
    
    @staticmethod
    def test_connection(host: str, username: str, password: str, timeout: int = 10) -> bool:
        """
        Test SSH connection.
        
        Returns:
            True jika connection berhasil, False jika gagal
        """
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(host, username=username, password=password, timeout=timeout)
            client.close()
            return True
        except:
            return False


