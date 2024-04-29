# Cumulocity First Device Agent

This is a hello-word Cumulocity client written in Python and leveraging MQTT for all communication with the service.

## Goals

☑ Procure a Cumulocity tenant  
☑ Create a device agent in Python, C/C++ or .net – Use MQTT protocol for the following tasks:  
🔴 Registers itself with certificate authentication (TIP: try basic authentication first)  
☑ Publishes data at regular intervals (choose freely such)  
☑ Receives control operations from Cumulocity (printing out the acknowledgement of the operation is enough)   
☑ Present measurement data in Cumulocity dashboard (Device Management or Cockpit is fine)  
☑ Set up smart rule to generate a simple alarm when measurement threshold exceeds a value.

## Documentation Starting Points

<https://cumulocity.com/guides/concepts/interfacing-devices/>

<https://cumulocity.com/guides/device-integration/introduction/>

## Prequisites

- Python 3
- [mqttx](https://mqttx.app/) CLI for MQTT testing. Or use what you prefer
- [openssl](https://www.openssl.org/) for TLS testing and cert/key generation
- [Eval Cumulocity tenant](https://www.cumulocity.com/pages/free-trial/)

## Prototyping Steps

I recommend prototyping with mqttx (or your favorite MQTT tool) before jumping into the code.

### Create a new user for the device

I could not use the user that was created for me when I signed up for Cumulocity. I did not spend a lot of time trying to debug this. Instead I created another user that was a member of the admins and business roles. Your userid for authentication will now be

```sh
TENANT-ID/DEVICE-USER
```

where TENANT-ID has been copied from the Cumulocity user dashboard and DEVICE-USER is the new user you just created.

The password is the password you just created.

### Confirm the ability to connect to the platform

The commands below all assume the following environment variables have been set

```sh
TENANT_ID
USER
PASS
```

Test a simple MQTT connection with 

```sh
mqttx conn -V 3.1.1 -h us.cumulocity.com -p 1883 -u ${TENANT_ID}/${USER} -P ${PASS}
```

Note the explicit use of MQTT v3.1.1. `mqttx` defaults to v5 and the Cumulocity platform wants v3.1.1. Also note for the initial test avoid additional challenges and use a clear (non TLS) connection. The Cumulocity documentation suggested I should prepend `mqtt` to the host name but I found this was uncessary.

Repeat the test with encryption only TLS

```sh
mqttx conn -V 3.1.1 -l mqtts -h us.cumulocity.com -p 8883 -u ${TENANT_ID}/${USER} -P ${PASS} --insecure
```

The `--insecure` switch tells `mqttx` to encrypt the connection and trust any server identity.

### Create a device

Per <https://cumulocity.com/docs/smartrest/mqtt-static-templates/>

> To ease device integration Cumulocity IoT already supports a number of static templates that can be used by any client without the need to create your own templates. These templates focus on the most commonly used messages for device management purposes.

The following command uses the `100` static template to create a device by publishing the message on the `s/us` topic

```sh
mqttx pub -V 3.1.1 -l mqtts -h us.cumulocity.com -p 8883 -u ${TENANT_ID}/${USER} -P ${PASS} -t 's/us' -m '100,A device,c8y_MQTTdevice' -i device-123 --insecure
```

Besides specifying the `100` static template, the `-i device-123` client id tells Cumulocity the device id. In this particular case, this is important because we only want the device created once.

### Enable pushing commands and configuration changes to device

Use the 114 static template to enable commands and configuration changes

```sh
mqttx pub -V 3.1.1 -l mqtts -h us.cumulocity.com -p 8883 -u ${TENANT_ID}/${USER} -P ${PASS} -t 's/us' -m '114,c8y_Command,c8y_Configuration' -i device-123 --insecure
sh

### Add a smart rule

I could not figure out how to create smart rules via MQTT or REST. See <https://cumulocity.com/docs/cockpit/smart-rules/> for how to create a smart rule via the portal.

### Rinse lather repeat

I found it easier to continue to prototype with mqttx and then translating that into Python, even for the `mqttx sub` scenarios.

## Trust the Server

Conveniently, `openssl` can be used to ask the server for its certificates. Inconveniently, a separate script is needed to separate out the certificates from the other output

```sh
echo | openssl s_client -showcerts -connect us.cumulocity.com:8883 | awk '/-----BEGIN CERTIFICATE-----/,/-----END CERTIFICATE-----/{if(/-----BEGIN CERTIFICATE-----/){a++}; out="/tmp/ca-"a".pem"; print > out}'
cat /tmp/ca-*.pem >/tmp/trusted-certs.pem
```

Now it is possible to verify the server

```sh
mqttx pub -V 3.1.1 -l mqtts -h us.cumulocity.com -p 8883 -u ${TENANT_ID}/${USER} -P ${PASS} -t 's/us' -m '100,A device,c8y_MQTTdevice' -i device-123 --ca /tmp/trusted-certs.pem
```

## Create a TLS Identity

I can create the TLS identities but I'm stuck on how to tell Cumulocity to trust me when I authenticate with the TLS identity. I've tried both a script a found in a Cumulocity related repo as well as creating a root CA and TLS identity as documented in the getting started pages. 

From what I have learned in the docs, the device CA cert must be uploaded to Cumulocity and verified by signing a message with the CA private key. When the device authenticates using a TLS identity, the device certificate must contain the device id and the full certificate chain must be sent to Cumulocity.

### The Cumulocity script

As I was exploring the Cumulocity docs I found a reference to <https://github.com/SoftwareAG/cumulocity-examples/tree/develop/mqtt-client/scripts>. The scripts will generate a CA and then sign a device certificate.

### Explicitly creating the CA and device identity

I followed <https://cumulocity.com/docs/device-integration/device-certificates/#generating-and-signing-certificates> with similar (lack of) success.

## Notes

- URL notation is misleading. Appending /mqtt to Python client as shown in the docs causes name resolution error. `mqtt` prefix to domain is also not necessary.
- Can't use email address as mqtt user
- Cannot use MQTT v5
- Deleting device quietly removes smart rule.
- Could not find API for smart rule
- REST API does not support MTLS
- <https://cumulocity.com/docs/device-integration/mqtt-examples/#to-copy-and-upload-the-certificate> incorrectly suggests uploading the device certificate as well as uploading the device certificate chain. Both of these are wrong as it's the CA cert that must be uploaded.
