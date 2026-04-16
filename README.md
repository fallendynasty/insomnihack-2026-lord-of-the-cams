# insomnihack-2026-lord-of-the-cams

This repo contains the files I used for a ctf challenge at insomnihack. The page talks about my learning process. This is a hardware/web challenge.

## Challenge Setup

The original description was:

> The lands are alive with stories, songs of heroes, tales of daring journeys, and laughter drifting through the halls. Amid the noise, a quiet hum stirs closer to home, weaving between the halls of data and the halls of stone. Those who pay attention to the smallest whispers, following their twists and turns, may stumble upon secrets hiding in plain sight. Curiosity and a careful step will reveal the hidden stream, waiting for the clever and patient to find its tale.

We were given a `.pcap` file and had to attack a physical box on-site. The key idea turned out to be combining traffic analysis with live recon against the device rather than treating them as separate problems.

## Initial Steps

At the start I was lazy, so I just dropped the pcap into claude and it told me the password was morder. For reference, I only have all free versions. Anyway I tried it on the device and it didn't work.

## What I Found On The Device

Because it's hardware, my first instinct was to connect to it.

I connected and ran a full port scan:

```bash
nmap -sV -p- 192.168.1.66 --open
```

The interesting results were:

```text
PORT     STATE SERVICE     VERSION
554/tcp  open  rtsp        D-Link DCS-2130 or Pelco IDE10DN webcam rtspd
9000/tcp open  cslistener?
Service Info: Device: webcam; CPE: cpe:/h:pelco:ide10dn
```

Initial observations:

- camera application running at port 554
- full port scan revealed port 9000, unknown service
- The username is `Sauron`

After this, I tried to hack into the services because I thought there were vulnerabilities inside. I also clauded on the device for a while and nothing work. In the end I thought the pcap was a red herring.

## Going back to the PCAP the old fashioned way

Anyway, I decided to look at the pcap manually in the end. I opened wireshark and there was a lot of protocol noise. I used AI to help strip away packet-header clutter and make the important application-layer values easier to read + fact check with wireshark.

Anyway here are some responses I got from the devices.

```text
DESCRIBE rtsp://192.168.1.66:554/h265Preview_01_main RTSP/1.0
Authorization: Digest username="Sauron", realm="BC Streaming Media", nonce="729612ffe9910096bdf06cf1f14191b7", uri="/h265Preview_01_main", response="<hash>"

RTSP/1.0 401 Unauthorized
WWW-Authenticate: Digest realm="BC Streaming Media", nonce="dd254a1bf54837d77c191359850451cf"
```

IDK what changed but after a while I realised/remembered MD5 is easy to crack offline, then combined with realising RTSP got its own authentication.

## This Is An Offline Crack

I stopped brute-forcing the service.

I went to search up how RTSP digest authentication works, something like:

```text
response = MD5( MD5(username:realm:password) : nonce : MD5(method:uri) )
```


## Building `crack_rtsp.py`

I got Claude generate a small helper script, `crack_rtsp.py`, that:

1. takes the RTSP digest components extracted from the capture
2. computes the fixed `HA2 = MD5(method:uri)`
3. iterates through a dictionary
4. computes `HA1 = MD5(username:realm:password)`
5. compares the final MD5 digest with the captured `response`

I used `rockyou.txt` because it is a standard wordlist I use from OSCP.

Then I got the password and got the flag by authenticating RTSP using VLC.

## What I learnt

- My free AI versions is not good enough, can't one shot everything.
- Must still use brain.
- Relook closely previous material you thought was a red herring.
- Learning about RTSP and digest.
- Use AI for small tasks like creating helper files and parsing files for clarity, don't expect it to do everything/higher level thinking (for now).

## Files In This Repo

- `OneDoesNotSimplyWalk-48c3e186bf748c94b9ae6ce8768479d0e42b71e556c760869c7c61fade2aafc1.pcap`: original packet capture from CTF description
- `crack_rtsp.py`: offline RTSP digest dictionary attack helper
- `rockyou.txt`: wordlist used during testing
