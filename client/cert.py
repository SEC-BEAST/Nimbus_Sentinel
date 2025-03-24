import ssl

# Example of using SSL with a self-signed certificate (Unsafe for production)
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Example of secure production setup
ssl_context_secure = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ssl_context_secure.check_hostname = True
ssl_context_secure.verify_mode = ssl.CERT_REQUIRED
ssl_context_secure.load_verify_locations('/etc/ssl/certs/ca-certificates.crt')  # Replace with your CA bundle path

# Example usage (replace with your own logic)
# connection = ssl_context_secure.wrap_socket(socket.socket(), server_hostname='example.com')

# Save and exit (Ctrl+X, then Y to confirm in nano editor)
