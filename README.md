# insomnihack-2026-lord-of-the-cams

This repository documents my learning process while working through a hardware-focused challenge that started with a packet capture and ended on a physical camera appliance.

## Challenge Setup

The original description was:

> The lands are alive with stories, songs of heroes, tales of daring journeys, and laughter drifting through the halls. Amid the noise, a quiet hum stirs closer to home, weaving between the halls of data and the halls of stone. Those who pay attention to the smallest whispers, following their twists and turns, may stumble upon secrets hiding in plain sight. Curiosity and a careful step will reveal the hidden stream, waiting for the clever and patient to find its tale.

We were given a `.pcap` file and had to attack a physical box on-site. The key idea turned out to be combining traffic analysis with live recon against the device rather than treating them as separate problems.

## What I Found On The Device

Once connected to the camera appliance, I ran a full port scan:

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

- `554/tcp` was clearly the camera application's RTSP service.
- `9000/tcp` was open but not immediately identifiable.
- The username visible during analysis was `Sauron`.

At this stage, the camera stream endpoint looked more promising than blind probing of the unknown service.

## What The PCAP Was Telling Me

The packet capture contained the useful part of the puzzle, but it was buried under a lot of protocol noise. I used AI to help strip away packet-header clutter and make the important application-layer values easier to read.

That made the relevant RTSP exchange much clearer:

```text
DESCRIBE rtsp://192.168.1.66:554/h265Preview_01_main RTSP/1.0
Authorization: Digest username="Sauron", realm="BC Streaming Media", nonce="729612ffe9910096bdf06cf1f14191b7", uri="/h265Preview_01_main", response="<hash>"
```

And when replaying the request format manually, the device answered:

```text
RTSP/1.0 401 Unauthorized
WWW-Authenticate: Digest realm="BC Streaming Media", nonce="dd254a1bf54837d77c191359850451cf"
```

This was the turning point. I initially went down the wrong path and treated it like a normal password guessing problem. I spent time considering obvious themed passwords such as `mordor`, but the real lesson was that RTSP here was using HTTP Digest-style authentication with an MD5-based response.

## The Important Learning: This Was An Offline Crack

The breakthrough was realizing that I did **not** need to brute-force the service interactively.

For this RTSP digest flow, the server gives enough information to verify password guesses offline. In the simplified form used here, the response is:

```text
response = MD5( MD5(username:realm:password) : nonce : MD5(method:uri) )
```

That changes the attack completely:

- no repeated online guesses against the camera
- no lockout/noise on the target service
- just calculate candidate hashes locally and compare them against the observed digest

Once I understood that, the `.pcap` stopped being "just traffic" and became a credential artifact.

## Building `crack_rtsp.py`

To test password candidates offline, I had Claude generate a small helper script, `crack_rtsp.py`, that:

1. takes the RTSP digest components extracted from the capture
2. computes the fixed `HA2 = MD5(method:uri)`
3. iterates through a dictionary
4. computes `HA1 = MD5(username:realm:password)`
5. compares the final MD5 digest with the captured `response`

I used `rockyou.txt` because it is a standard wordlist I already knew from OSCP prep and earlier practice.

The value of the script was not sophistication. It was speed: once the auth scheme was understood correctly, a short script was enough to validate the idea and move forward.

## Why This Was A Good Lesson

This challenge reinforced a few things for me:

- Traffic captures can contain reusable authentication material, not just network metadata.
- Understanding the protocol beats guessing. I lost time thinking in terms of "what is the password?" instead of "how is the password verified?"
- AI was useful here as a parsing and clarity aid. It helped extract the signal from noisy packet data, but the important step was still understanding the digest workflow.
- Wordlists are only effective when paired with the correct verification model. `rockyou.txt` only became useful after the authentication math was clear.

## Notes For Future Improvement

This repository is the start of a cleaner write-up. Good next additions would be:

- a sanitized walk-through of the exact fields extracted from the `.pcap`
- a short explanation of why the unknown service on `9000/tcp` was deprioritized
- a redacted example showing how to compute the digest step by step
- the final post-authentication path on the physical box, if I decide to document that too

## Files In This Repo

- `OneDoesNotSimplyWalk-48c3e186bf748c94b9ae6ce8768479d0e42b71e556c760869c7c61fade2aafc1.pcap`: original packet capture
- `crack_rtsp.py`: offline RTSP digest dictionary attack helper
- `rockyou.txt`: wordlist used during testing
