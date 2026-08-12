# Troubleshooting

## API login fails

- Verify the EVE web UI is reachable.
- Check Community vs Pro protocol.
- Try HTTP for Community or HTTPS for Pro as appropriate.
- Confirm the account is not simultaneously used by another API/browser session if session behavior causes a conflict.

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
