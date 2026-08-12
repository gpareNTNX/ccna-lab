# Troubleshooting

## API login fails

- Verify the EVE web UI is reachable.
- Use the EVE-NG Web/API account, not the Linux SSH account.
- Check Community vs Pro protocol.
- Use HTTP for Community or HTTPS for Pro as appropriate.

## SSH works but API login fails

SSH and the EVE-NG Web/API are separate authentication domains. A typical installation uses `root` for SSH/CLI and `admin` for the Web/API. Use the same Web/API username and password that work in your browser.

For Community, use HTTP unless your deployment was customized. For Pro, enable HTTPS in the application; the client includes `html5=0` in the login payload.

To test the API outside the application:

Community:

```bash
curl -s -c /tmp/eve-cookie -b /tmp/eve-cookie -X POST \
  -d '{"username":"admin","password":"YOUR_WEB_PASSWORD"}' \
  http://EVE_IP/api/auth/login
```

Pro:

```bash
curl -k -s -c /tmp/eve-cookie -b /tmp/eve-cookie -X POST \
  -d '{"username":"admin","password":"YOUR_WEB_PASSWORD","html5":"0"}' \
  https://EVE_IP/api/auth/login
```

A successful response has `status: success`.

## API returns 412 / session timed out (90001)

EVE-NG allows only one active Web/API session per user. Logging into the same EVE-NG user from another browser or location invalidates the previous session.

Typical error:

```text
EVE API POST /labs: HTTP 412:
User is not authenticated or session timed out (90001)
```

The application now automatically re-authenticates once and retries the failed request. If a browser repeatedly logs in with the same user, however, the browser and the application can continue invalidating each other's sessions.

Recommended setup:

```text
SSH / CLI
  Username: root (or another SSH-capable account)

EVE Web / API
  Username: a dedicated EVE-NG API user
```

If you use `admin` for the application, avoid simultaneously logging into the EVE-NG Web UI with the same `admin` account while the application is creating or managing labs.

## SSH works but image install fails

Verify the SSH user can write to:

```text
/opt/unetlab/addons/qemu/
```

and can run:

```text
/opt/unetlab/wrappers/unl_wrapper -a fixpermissions
```

## IOSv node does not appear

Confirm the folder begins with `vios-`.

## IOSvL2 node does not appear

Confirm the folder begins with `viosl2-`.

## Node boots but validator cannot connect

- Start the node first.
- Wait for IOS to finish booting.
- Verify the node API exposes a Telnet console URL.
- Check that SSH remains connected.

## Experimental cabling fails

Disable **experimental API cabling** and cable the nodes in the EVE-NG web UI. The rest of V4 remains usable.
