import telnetlib3
import asyncio
from time import sleep
import re

# Akses OLT
print("#####################2####################################")
print("# APLIKASI AUTO-CONFIGURE ONT BY DIMAS #")
print("#########################################################")
print("Pilih OLT yang akan dikonfigurasi")
print(" ├── 1. BOYOLANGU")
print(" ├── 2. BEJI")
print(" ├── 3. DURENAN")
print(" ├── 4. KALIDAWIR")
print(" ├── 5. KAUMAN")
print(" ├── 6. KEDIRI")
print(" ├── 7. CAMPUR BARU")
print(" ├── 8. BLITAR")
print(" └── 9. GANDUSARI")

olt = int(input("👀 MASUKKAN PILIHAN : "))
username = 'n0c'
password = 'j46u4r@2025'
c600 = False
match(olt):
    case 1:
        ip = "192.168.12.1"
        vlan = "901"
        olt_name = "BOYOLANGU"
    case 2:
        ip = "192.168.12.5"
        vlan = "903"
        olt_name = "BEJI"
    case 3:
        ip = "192.168.12.6"
        vlan = "911"
        olt_name = "DURENAN"
    case 4:
        ip = "192.168.12.7"
        vlan = "902"
        olt_name = "KALIDAWIR"
    case 5:
        ip = "192.168.12.4"
        vlan = "920"
        olt_name = "KAUMAN"
    case 6:
        ip = "192.168.12.8"
        vlan = "905"
        olt_name = "KEDIRI"
    case 7:
        ip = "192.168.12.9"
        c600 = True
        vlan = "911"
        olt_name = "CAMPUR"
    case 8:
        ip = "192.168.12.2"
        vlan = "904"
        olt_name = "BLITAR"
    case 9:
        ip = "192.168.12.3"
        vlan = "906"
        olt_name = "GANDUSARI"
    case _:
        print('Maaf, input tidak dimengerti')
        exit()

async def main():
    reader, writer = await telnetlib3.open_connection(ip, 23)
    writer.write(username + '\n')
    sleep(0.5)
    writer.write(password + '\n')
    uncfg_ONT = []
    while True:
        if c600:
            writer.write("show pon onu uncfg" + '\n')
            try:
                while True:
                    output = await asyncio.wait_for(reader.readline(), 2)
                    if 'GPON' in output:
                        uncfg_ONT.append(output)
            except asyncio.exceptions.TimeoutError:
                pass
        else:
            writer.write("show gpon onu uncfg" + '\n')
            try:
                while True:
                    output = await asyncio.wait_for(reader.readline(), 2)
                    if 'unknown' in output:
                        uncfg_ONT.append(output)
            except asyncio.exceptions.TimeoutError:
                pass
        if uncfg_ONT == []:
            print("Unconfigured ONT tidak terdeteksi")
            cek = input("Apakah anda ingin mencoba deteksi ulang(Y/N)? ").upper()
            match(cek):
                case 'Y':
                    pass
                case 'N':
                    return None
                case _:
                    print('Maaf, input tidak dimengerti')
                    return None
        else:
            break
    
    listed_uncfg = []
    for item in uncfg_ONT:
        if c600:
            x = item.replace("    ", " ")
            x = x.replace(" ", ';')
            splitter_1 = re.split(";", x)
            splitter_2 = re.split("/", splitter_1[0])
            if int(splitter_2[2]) < 10:
                if int(splitter_2[2]) < 10:
                    sn = splitter_1[2]
                else:
                    sn = splitter_1[1]
            else:
                sn = splitter_1[1]
            while True:
                cek = input(f"Apakah {sn} adalah yang dicari(Y/N)? ").upper()
                match(cek):
                    case 'Y':
                        listed_uncfg.append(sn)
                        listed_uncfg.append(splitter_2[1])
                        listed_uncfg.append(splitter_2[2])
                        break
                    case 'N':
                        break
                    case _:
                        print("Maaf input hanya Y atau N")
            if listed_uncfg != []:
                break
        else:
            x = item.replace("        ", " ")
            x = x.replace(" ", ';')
            splitter_1 = re.split(";", x)
            splitter_2 = re.split("/", splitter_1[0])
            splitter_3 = re.split(":", splitter_2[2])
            if int(splitter_3[0]) < 10:
                sn = splitter_1[2]
            else:
                sn = splitter_1[1]
            while True:
                cek = input(f"Apakah {sn} adalah yang dicari(Y/N)? ").upper()
                match(cek):
                    case 'Y':
                        listed_uncfg.append(sn)
                        listed_uncfg.append(splitter_2[1])
                        listed_uncfg.append(splitter_3[0])
                        break
                    case 'N':
                        break
                    case _:
                        print("Maaf input hanya Y atau N")
            if listed_uncfg != []:
                break

    if listed_uncfg == []:
        print("Maaf SN tidak ditemukan")
        return None
    else:
        print("\nMengecek utilisasi bandwidth pada port OLT...")
        writer.write("terminal length 0\n")
        await asyncio.sleep(0.3)
        writer.write(f"show pon bandwidth dba interface gpon-olt_1/{listed_uncfg[1]}/{listed_uncfg[2]}\n")
        await asyncio.sleep(1)

        rate_percentage = 0.0
        THRESHOLD_RATE = 75.0

        try:
            while True:
                output_bw = await asyncio.wait_for(reader.readline(), 3)
                if '#' in output_bw or '>' in output_bw or "invalid" in output_bw.lower():
                    break
                match_rate = re.search(r'gpon-olt_1/' + re.escape(listed_uncfg[1]) + r'/' + re.escape(listed_uncfg[2]) + r'\s+1\(GPON\)\s+\d+\s+\d+\s+(\d+\.\d+)%', output_bw)
                if match_rate:
                    rate_percentage = float(match_rate.group(1))
                    break
        except asyncio.exceptions.TimeoutError:
            pass

        dba_profile_suffix = "MBW"
        if rate_percentage < THRESHOLD_RATE:
            dba_profile_suffix = "FIX"

        prev_onu = None
        print("1. F670L")
        print("2. C-DATA")
        while True:
            modem = int(input("🛜 Pilih Jenis Modem : "))
            match(modem):
                case 1:
                    jenismodem = "ZTE"
                    break
                case 2:
                    jenismodem = "C-DATA"
                    break
                case _:
                    print("Maaf input tidak dimengerti")
        writer.write("terminal length 200\n")
        await asyncio.sleep(0.3)

        calculation = "1"
        prev_onu = None
        if c600:
            identifier = 'enable'
            writer.write(f"show gpon onu state gpon_olt-1/{listed_uncfg[1]}/{listed_uncfg[2]}\n")
        else:
            identifier = '1(GPON)'
            writer.write(f"show gpon onu state gpon-olt_1/{listed_uncfg[1]}/{listed_uncfg[2]}\n")
        
        try:
            while True:
                output = await asyncio.wait_for(reader.readline(), 2)

                if "no related information to show" in output.lower() or "error" in output.lower():
                    calculation = "1"
                    print(f"Onu kosong pada 1/{listed_uncfg[1]}/{listed_uncfg[2]}:1")
                    break
                
                if '#' in output or '>' in output:
                    if prev_onu is None:
                        print(f"Onu kosong pada 1/{listed_uncfg[1]}/{listed_uncfg[2]}:1")
                        calculation = "1"
                    else:
                        calculation = prev_onu + 1
                        print(f"Onu kosong pada 1/{listed_uncfg[1]}/{listed_uncfg[2]}:{calculation}")
                    break

                if identifier in output:
                    try:
                        parts = re.split(" ", output.strip())
                        if len(parts) > 0:
                            onu_port_str = parts[0]
                            onu_parts = onu_port_str.split(":")
                            if len(onu_parts) > 1:
                                current_onu = int(onu_parts[1])
                                if prev_onu is not None and current_onu > prev_onu + 1:
                                    calculation = prev_onu + 1
                                    print(f"Onu kosong pada 1/{listed_uncfg[1]}/{listed_uncfg[2]}:{calculation}")
                                    break
                                prev_onu = current_onu
                    except (ValueError, IndexError):
                        continue
                elif "ONU Number:" in output:
                    if prev_onu is not None:
                        calculation = prev_onu + 1
                        print(f"Onu kosong pada 1/{listed_uncfg[1]}/{listed_uncfg[2]}:{calculation}")
                    else:
                        calculation = "1"
                        print(f"Onu kosong pada 1/{listed_uncfg[1]}/{listed_uncfg[2]}:1")
                    break

        except asyncio.exceptions.TimeoutError:
            print(f"Timeout: Tidak ada ONU terdeteksi pada port 1/{listed_uncfg[1]}/{listed_uncfg[2]}.")
            print(f"Asumsi ONU kosong: 1")
            calculation = "1"

        nama_pelanggan = input("👤 MASUKKAN NAMA PELANGGAN : ")
        alamat = input("📍 MASUKKAN ALAMAT PELANGGAN : ")
        pppoe = input("🌐 MASUKKAN NOMOR ID PELANGGAN : ")
        pass_ONT = input("🔒 MASUKKAN PASSWORD PPPOE : ")
        print("1. 10M")
        print("2. 15M")
        print("3. 20M")
        print("4. 25M")
        print("5. 30M")
        print("6. 35M")
        print("7. 40M")
        print("8. 45M")
        print("9. 50M")
        print("10. 75M")
        print("11. 100M")
        cek = int(input("PILIH PAKET PELANGGAN : "))

        match(cek):
            case 1:
                paket = "10"
            case 2:
                paket = "15"
            case 3:
                paket = "20"
            case 4:
                paket = "25"
            case 5:
                paket = "30"
            case 6:
                paket = "35"
            case 7:
                paket = "40"
            case 8:
                paket = "45"
            case 9:
                paket = "50"
            case 10:
                paket = "75"
            case 11:
                paket = "100"
            case _:
                print("Paket internet tidak ditemukan")
                return None

        print("PROSES KONFIGURASI.....")
        if c600:
            writer.write("configure terminal\n")
            await asyncio.sleep(0.3)
            if jenismodem == "C-DATA":
                writer.write(f"interface gpon_olt-1/{listed_uncfg[1]}/{listed_uncfg[2]}\n")
                await asyncio.sleep(0.3)
                writer.write(f"onu {calculation} type ALL sn {listed_uncfg[0]}\n")
                sleep(1.5)
                writer.write("exit\n")
                await asyncio.sleep(0.3)
                writer.write(f"interface gpon_onu-1/{listed_uncfg[1]}/{listed_uncfg[2]}:{calculation}\n")
                await asyncio.sleep(0.3)
                writer.write(f"name {nama_pelanggan}\n")
                await asyncio.sleep(0.3)
                writer.write(f"description {alamat}\n")
                await asyncio.sleep(0.3)
                writer.write(f"tcont 1 name PPPOE profile UP-{paket}MB-{dba_profile_suffix}\n")
                await asyncio.sleep(0.3)
                writer.write("gemport 1 name PPPOE tcont 1\n")
                await asyncio.sleep(0.3)
                writer.write(f"exit\n")
                await asyncio.sleep(0.3)
                writer.write(f"interface vport-1/{listed_uncfg[1]}/{listed_uncfg[2]}.{calculation}:1\n")
                await asyncio.sleep(0.3)
                writer.write(f"service-port 1 user-vlan {vlan} vlan {vlan}\n")
                await asyncio.sleep(0.3)
                writer.write(f"qos traffic-policy DOWN-{paket} direction egress\n")
                await asyncio.sleep(0.3)
                writer.write("exit\n")
                await asyncio.sleep(0.3)
                writer.write(f"pon-onu-mng gpon_onu-1/{listed_uncfg[1]}/{listed_uncfg[2]}:{calculation}\n")
                await asyncio.sleep(0.3)
                writer.write(f"service CIGNAL gemport 1 vlan {vlan}\n")
                await asyncio.sleep(0.3)
                writer.write(f"wan-ip ipv4 mode pppoe username {pppoe} password {pass_ONT} vlan-profile vlan{vlan} host 1\n")
                await asyncio.sleep(0.3)
                writer.write("security-mgmt 2 ingress-type wan mode forward state enable protocol web\n")
                await asyncio.sleep(0.3)
                writer.write(f"int eth eth_0/1 sta lock\n")
                await asyncio.sleep(0.3)
                writer.write(f"int eth eth_0/2 sta lock\n")
                await asyncio.sleep(0.3)
                writer.write(f"int eth eth_0/3 sta lock\n")
                await asyncio.sleep(0.3)
                writer.write(f"int eth eth_0/4 sta lock\n")
                await asyncio.sleep(0.3)
                writer.write(f"exit\n")
                await asyncio.sleep(0.3)
            else: 
                writer.write(f"interface gpon_olt-1/{listed_uncfg[1]}/{listed_uncfg[2]}\n")
                await asyncio.sleep(0.3)
                writer.write(f"onu {calculation} type ALL sn {listed_uncfg[0]}\n")
                sleep(1.5)
                writer.write("exit\n")
                await asyncio.sleep(0.3)
                writer.write(f"interface gpon_onu-1/{listed_uncfg[1]}/{listed_uncfg[2]}:{calculation}\n")
                writer.write(f"name {nama_pelanggan}\n")
                await asyncio.sleep(0.3)
                writer.write(f"description {alamat}\n")
                await asyncio.sleep(0.3)
                writer.write(f"tcont 1 name PPPOE profile UP-{paket}MB-{dba_profile_suffix}\n")
                await asyncio.sleep(0.3)
                writer.write("gemport 1 name PPPOE tcont 1\n")
                await asyncio.sleep(0.3)
                writer.write("exit\n")
                await asyncio.sleep(0.3)
                writer.write(f"interface vport-1/{listed_uncfg[1]}/{listed_uncfg[2]}.{calculation}:1\n")
                await asyncio.sleep(0.3)
                writer.write(f"service-port 1 user-vlan {vlan} vlan {vlan}\n")
                await asyncio.sleep(0.3)
                writer.write(f"qos traffic-policy DOWN-{paket} direction egress\n")
                await asyncio.sleep(0.3)
                writer.write(f"exit\n")
                await asyncio.sleep(0.3)
                writer.write(f"pon-onu-mng gpon_onu-1/{listed_uncfg[1]}/{listed_uncfg[2]}:{calculation}\n")
                await asyncio.sleep(0.3)
                writer.write(f"service CIGNAL gemport 1 vlan {vlan}\n")
                await asyncio.sleep(0.3)
                writer.write(f"wan-ip 1 ipv4 mode pppoe username {pppoe} password {pass_ONT} vlan-profile vlan{vlan} host 1\n")
                await asyncio.sleep(0.3)
                writer.write(f"wan-ip 1 ipv4 ping-response enable traceroute-response enable\n")
                await asyncio.sleep(0.3)
                writer.write(f"security-mgmt 2 ingress-type wan mode forward state enable protocol web\n")
                await asyncio.sleep(0.3)
                writer.write(f"int eth eth_0/1 sta lock\n")
                await asyncio.sleep(0.3)
                writer.write(f"int eth eth_0/2 sta lock\n")
                await asyncio.sleep(0.3)
                writer.write(f"int eth eth_0/3 sta lock\n")
                await asyncio.sleep(0.3)
                writer.write(f"int eth eth_0/4 sta lock\n")
                await asyncio.sleep(0.3)
                writer.write(f"exit\n")
                await asyncio.sleep(0.3)
        else:  # Not C300 (likely Fiberhome)
            if jenismodem == "ZTE":
                writer.write("configure terminal\n")
                await asyncio.sleep(0.3)
                writer.write(f"interface gpon-olt_1/{listed_uncfg[1]}/{listed_uncfg[2]}\n")
                await asyncio.sleep(0.3)
                writer.write(f"onu {calculation} type ZTEG-F609 sn {listed_uncfg[0]} vport-mode gemport\n")
                sleep(1.5)
                writer.write("exit\n")
                await asyncio.sleep(0.3)
                writer.write(f"interface gpon-onu_1/{listed_uncfg[1]}/{listed_uncfg[2]}:{calculation}\n")
                await asyncio.sleep(0.3)
                writer.write(f"name {nama_pelanggan}\n")
                await asyncio.sleep(0.3)
                writer.write(f"description {alamat}\n")
                await asyncio.sleep(0.3)
                writer.write(f"tcont 1 name PPPOE profile UP-{paket}MB-{dba_profile_suffix}\n")
                await asyncio.sleep(0.3)
                writer.write("gemport 1 name PPPOE tcont 1\n")
                await asyncio.sleep(0.3)
                writer.write(f"gemport 1 traffic-limit downstream DOWN-{paket}\n")
                await asyncio.sleep(0.3)
                writer.write("switchport mode hybrid vport 1\n")
                await asyncio.sleep(0.3)
                writer.write(f"service-port 1 vport 1 user-vlan {vlan} vlan {vlan}\n")
                await asyncio.sleep(0.3)
                writer.write("port-identification format DSL-FORUM-PON vport 1\n")
                await asyncio.sleep(0.3)
                writer.write("pppoe-intermediate-agent enable vport 1\n")
                await asyncio.sleep(0.3)
                writer.write("exit\n")
                await asyncio.sleep(0.3)
                writer.write(f"pon-onu-mng gpon-onu_1/{listed_uncfg[1]}/{listed_uncfg[2]}:{calculation}\n")
                await asyncio.sleep(0.3)
                writer.write("flow mode 1 tag-filter vlan-filter untag-filter discard\n")
                await asyncio.sleep(0.3)
                writer.write("flow mode 255 tag-filter vlan-filter untag-filter discard\n")
                await asyncio.sleep(0.3)
                writer.write(f"flow 1 pri 0 vlan {vlan}\n")
                await asyncio.sleep(0.3)
                writer.write("gemport 1 flow 1\n")
                await asyncio.sleep(0.3)
                writer.write("switchport-bind switch_0/1 iphost 1\n")
                await asyncio.sleep(0.3)
                writer.write("vlan-filter-mode ethuni eth_0/3 tag-filter vlan-filter untag-filter discard\n")
                await asyncio.sleep(0.3)
                writer.write(f"vlan-filter ethuni eth_0/3 pri 0 vlan {vlan}\n")
                await asyncio.sleep(0.3)
                writer.write(f"onu-vlan ethuni eth_0/3 up-mode add up-pri 0 up-vlan {vlan} down-mode transparent\n")
                await asyncio.sleep(0.3)
                writer.write(f"pppoe 1 nat enable user {pppoe} password {pass_ONT}\n")
                await asyncio.sleep(0.3)
                writer.write(f"onu-vlan iphost 1 up-mode add up-pri 0 up-vlan {vlan} down-mode transparent\n")
                await asyncio.sleep(0.3)
                writer.write("vlan-filter-mode iphost 1 tag-filter vlan-filter untag-filter transparent\n")
                await asyncio.sleep(0.3)
                writer.write(f"vlan-filter iphost 1 pri 0 vlan {vlan}\n")
                await asyncio.sleep(0.3)
                writer.write("security-mgmt 2 ingress-type wan mode forward state enable protocol web\n")
                await asyncio.sleep(0.3)
                writer.write(f"int eth eth_0/1 sta lock\n")
                await asyncio.sleep(0.3)
                writer.write(f"int eth eth_0/2 sta lock\n")
                await asyncio.sleep(0.3)
                writer.write(f"int eth eth_0/3 sta lock\n")
                await asyncio.sleep(0.3)
                writer.write(f"int eth eth_0/4 sta lock\n")
                await asyncio.sleep(0.3)
                writer.write("exit\n")
                await asyncio.sleep(0.3)
            else:  # This is likely for Fiberhome C-DATA or other types not specifically ZTE on Fiberhome OLT
                writer.write("configure terminal\n")
                await asyncio.sleep(0.3)
                writer.write(f"interface gpon-olt_1/{listed_uncfg[1]}/{listed_uncfg[2]}\n")
                await asyncio.sleep(0.3)
                writer.write(f"onu {calculation} type ZTEG-F609 sn {listed_uncfg[0]}\n")
                sleep(1.5)
                writer.write("exit\n")
                await asyncio.sleep(0.3)
                writer.write(f"interface gpon-onu_1/{listed_uncfg[1]}/{listed_uncfg[2]}:{calculation}\n")
                writer.write(f"name {nama_pelanggan}\n")
                await asyncio.sleep(0.3)
                writer.write(f"description {alamat}\n")
                await asyncio.sleep(0.3)
                writer.write(f"tcont 1 name PPPOE profile UP-{paket}MB-{dba_profile_suffix}\n")
                await asyncio.sleep(0.3)
                writer.write("gemport 1 name PPPOE tcont 1\n")
                await asyncio.sleep(0.3)
                writer.write(f"gemport 1 traffic-limit downstream DOWN-{paket}M\n")
                await asyncio.sleep(0.3)
                writer.write("encrypt 1 enable downstream\n")
                await asyncio.sleep(0.3)
                writer.write(f"service-port 1 vport 1 user-vlan {vlan} vlan {vlan}\n")
                await asyncio.sleep(0.3)
                writer.write(f"exit\n")
                await asyncio.sleep(0.3)
                writer.write(f"pon-onu-mng gpon-onu_1/{listed_uncfg[1]}/{listed_uncfg[2]}:{calculation}\n")
                await asyncio.sleep(0.3)
                writer.write(f"service CIGNAL gemport 1 vlan {vlan}\n")
                await asyncio.sleep(0.3)
                writer.write(f"wan-ip 1 mode pppoe username {pppoe} password {pass_ONT} vlan-profile vlan{vlan} host 1\n")
                await asyncio.sleep(0.3)
                writer.write(f"wan-ip 1 ping-response enable traceroute-response enable\n")
                await asyncio.sleep(0.3)
                writer.write(f"tr069-mgmt 1 state unlock\n")
                await asyncio.sleep(0.3)
                writer.write(f"tr069-mgmt 1 acs http://103.183.99.86:9999/v1/acs validate basic username acs password acs\n")
                await asyncio.sleep(0.3)
                writer.write("security-mgmt 2 ingress-type wan mode forward state enable protocol web\n")
                await asyncio.sleep(0.3)
                writer.write("int eth eth_0/1 sta lock\n")
                await asyncio.sleep(0.3)
                writer.write("int eth eth_0/2 sta lock\n")
                await asyncio.sleep(0.3)
                writer.write("int eth eth_0/3 sta lock\n")
                await asyncio.sleep(0.3)
                writer.write("int eth eth_0/4 sta lock\n")
                await asyncio.sleep(0.3)

        try:
            while True:
                output2 = await asyncio.wait_for(reader.readline(), 2)
                print(output2)
        except asyncio.exceptions.TimeoutError:
            pass
        print("KONFIGURASI SELESAI")
        print(f"✅ Serial Number : {listed_uncfg[0]}")
        print(f"✅ ID pelanggan : {pppoe}")
        print(f"✅ Nama pelanggan : {nama_pelanggan}")
        print(f"✅ OLT dan ONU : {olt_name} 1/{listed_uncfg[1]}/{listed_uncfg[2]}:{calculation}")
        print(f"✅ DBA Profile Used : {dba_profile_suffix}")

        writer.write("exit\n")
        await asyncio.sleep(0.5)
        writer.close()

asyncio.run(main())
