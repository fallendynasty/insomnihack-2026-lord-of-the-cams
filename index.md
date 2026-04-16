---
layout: default
---

# Lord of the Cams

## Hardware Recon, PCAP Analysis, and RTSP Digest Cracking

This page documents my learning process while working through a hardware-focused challenge that started with a packet capture and led to a physical camera device on-site.

### Challenge Prompt

> The lands are alive with stories, songs of heroes, tales of daring journeys, and laughter drifting through the halls. Amid the noise, a quiet hum stirs closer to home, weaving between the halls of data and the halls of stone. Those who pay attention to the smallest whispers, following their twists and turns, may stumble upon secrets hiding in plain sight. Curiosity and a careful step will reveal the hidden stream, waiting for the clever and patient to find its tale.

We were given a `.pcap` file and needed to compromise a physical box. The challenge turned out to reward careful protocol understanding more than aggressive guessing.

### Live Recon

On the physical device, I started with a full TCP scan:

```bash
nmap -sV -p- 192.168.1.66 --open
```

Results:

```text
PORT     STATE SERVICE     VERSION
554/tcp  open  rtsp        D-Link DCS-2130 or Pelco IDE10DN webcam rtspd
9000/tcp open  cslistener?
Service Info: Device: webcam; CPE: cpe:/h:pelco:ide10dn
```

That immediately suggested a camera stream service on `554/tcp` and a second, less obvious service on `9000/tcp`.

### Extracting Signal From The PCAP

The `.pcap` held the important clue, but the useful data was buried under normal packet and protocol overhead. I used AI to help reformat the traffic into something easier to reason about, especially around the RTSP authentication fields.

The relevant traffic looked like this:

```text
DESCRIBE rtsp://192.168.1.66:554/h265Preview_01_main RTSP/1.0
Authorization: Digest username="Sauron", realm="BC Streaming Media", nonce="729612ffe9910096bdf06cf1f14191b7", uri="/h265Preview_01_main", response="<hash>"
```

The username `Sauron` was visible, and the server challenge identified digest authentication:

```text
RTSP/1.0 401 Unauthorized
WWW-Authenticate: Digest realm="BC Streaming Media", nonce="dd254a1bf54837d77c191359850451cf"
```

### The Wrong Assumption

At first I treated the problem like ordinary password guessing. I spent time considering themed passwords, including `mordor`, and thinking in terms of online brute force.

That was the wrong model.

### The Actual Breakthrough

The key realization was that RTSP here was using an MD5-based digest authentication scheme. That means the password is not sent directly, but the capture contains enough data to verify candidate passwords offline.

For the simplified digest flow seen here:

```text
response = MD5( MD5(username:realm:password) : nonce : MD5(method:uri) )
```

Once I understood that, the problem changed completely:

- the camera no longer needed to be hammered with guesses
- the packet capture itself became the target artifact
- a wordlist attack could be performed locally and quietly

### Offline Cracking Script

I then used Claude to help generate `crack_rtsp.py`, a small script that:

1. loads the digest parameters recovered from the traffic
2. computes `HA2 = MD5(method:uri)`
3. reads candidate passwords from a wordlist
4. computes `HA1 = MD5(username:realm:password)`
5. generates the final digest and compares it to the captured response

I used `rockyou.txt` because it was familiar from prior OSCP-style study and was a reasonable first dictionary for this kind of challenge.

### What I Learned

- Protocol understanding matters more than guessing speed.
- Packet captures can leak reusable authentication material.
- AI was helpful for reducing noise and making the traffic readable, but it did not replace the need to understand the authentication flow.
- The right wordlist only becomes useful once the verification logic is correct.

### Repo Contents

- `README.md` contains the repository version of this write-up.
- `index.md` provides a simple GitHub Pages landing page.
- `crack_rtsp.py` contains the offline digest-checking helper.
- `OneDoesNotSimplyWalk-48c3e186bf748c94b9ae6ce8768479d0e42b71e556c760869c7c61fade2aafc1.pcap` is the original packet capture.
