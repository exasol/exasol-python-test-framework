# Exasol Python Test Framework 0.6.0, released 2024-07-08

Code name: Configure TLS certificate validation

## Summary

This release adds a CLI option controlling parameter `SSLCERTIFICATE` in file `odbc.ini`.

Additionally, the release fixes vulnerabilities by updating dependencies:
* CVE-2024-35195 in dependency `requests` in versions < `2.32.0` caused by requests `Session` object not verifying requests after making first request with `verify=False`
* CVE-2024-37891 in transitive dependency via `boto3` to `urllib3` in versions < `2.2.2` caused by proxy-authorization request header not to be stripped during cross-origin redirects as no update of notebook-connector is available, yet.
* GHSA-w235-7p84-xx57 in transitive dependency via `luigi` to `tornado` in versions < `6.4.1` enabling CRLF injection in `CurlAsyncHTTPClient` headers.
* GHSA-753j-mpmx-qq6g in transitive dependency via `luigi` to `tornado` in versions < `6.4.1` due to inconsistent interpretation of HTTP Requests ('HTTP Request/Response Smuggling')

However, the release ignores the following vulnerabilities
* GHSA-753j-mpmx-qq6g in dependency `configobj` in versions &le; `5.0.8` being ReDoS exploitable by developers using values in a server-side configuration file as SLCT is used only client side and a patched version is not available, yet.

## Security Fixes

* #70: Fixed vulnerabilities by updating dependencies.

## Features

* #66: Added CLI option controlling parameter `SSLCERTIFICATE` in file `odbc.ini`.
