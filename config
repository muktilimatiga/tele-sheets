import telnetlib3
import asyncio
from time import sleep
import re

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

async def connect_to_olt(ip, username, password):
    print("Menghubungkan ke OLT...")
    reader, writer = await telnetlib3.open_connection(ip, 23)
    writer.write(username + '\n')
    await asyncio.sleep(0.5)
    writer.write(password + '\n')
    await asyncio.sleep(0.5)
    return reader, writer

async def find_uncfg_onu(reader, writer, c600):
    uncfg_ONT = []
    while True:
        if c600:
            writer.write("show pon onu uncfg" + '\n')
            identifier = 'GPON'
        else:
            writer.write("show gpon onu uncfg" + '\n')
            identifier = 'unknown'
        try:
            while True:
                output = await asyncio.wait_for(reader.readline(), 2)
                if identifier in output:
                    uncfg_ONT.append(output)
        except asyncio.exceptions.TimeoutError:
            pass
        if not uncfg_ONT:
            print("Unconfigured ONT tidak terdeteksi")
            cek = input("Apakah anda ingin mencoba deteksi ulang(Y/N)? ").upper()
            if cek != 'Y':
                return None
        else:
            break
    for item in uncfg_ONT:
        if c600:
            x = item.replace("    ", " ").replace(" ", ';')
            splitter_1 = re.split(";", x)
            splitter_2 = re.split("/", splitter_1[0])
            sn = splitter_1[2] if int(splitter_2[2]) < 10 else splitter_1[1]
        else:
            x = item.replace("        ", " ").replace(" ", ';')
            splitter_1 = re.split(";", x)
            splitter_2 = re.split("/", splitter_1[0])
            splitter_3 = re.split(":", splitter_2[2])
            sn = splitter_1[2] if int(splitter_3[0]) < 10 else splitter_1[1]
        while True:
            cek = input(f"Apakah {sn} adalah yang dicari(Y/N)? ").upper()
            if cek == 'Y':
                slot = splitter_2[1]
                port = splitter_2[2] if c600 else splitter_3[0]
                return [sn, slot, port]
            elif cek == 'N':
                break
            else:
                print("Maaf input hanya Y atau N")
    print("Maaf SN tidak ditemukan")
    return None

async def get_onu_placement(reader, writer, listed_uncfg, c600):
    prev_onu = None
    calculation = None
    
    writer.write("terminal length 0\n")
    await asyncio.sleep(0.3)
    
    if c600:
        writer.write(f"show gpon onu state gpon_olt-1/{listed_uncfg[1]}/{listed_uncfg[2]}\n")
    else:
        writer.write(f"show gpon onu state gpon-olt_1/{listed_uncfg[1]}/{listed_uncfg[2]}\n")
    
    try:
        while True:
            output = await asyncio.wait_for(reader.readline(), 2)
            print(output.strip()) 
            
            onu_match = None
            if c600:
                onu_match = re.search(r'GPON-ONu_1/(\d+)/(\d+):(\d+)', output)
            else:
                onu_match = re.search(r'(\d+)/(\d+)/(\d+):(\d+)', output)

            if onu_match:
                onu_id = int(onu_match.group(4))

                if prev_onu is None:
                    prev_onu = onu_id
                
                if onu_id - prev_onu > 1:
                    calculation = prev_onu + 1
                    print(f"Onu kosong pada 1/{listed_uncfg[1]}/{listed_uncfg[2]}:{calculation}")
                    break
                
                prev_onu = onu_id

    # === Check slot status ===
            elif "ONU Number:" in output:
                match_onu_count = re.search(r'ONU Number:\s+\d+/(\d+)', output)
                if match_onu_count:
                    total_onus = int(match_onu_count.group(1))
                    if total_onus == 128:
                        print("SLOT TERSEBUT PENUH :(")
                        return None
                    else:

                        calculation = prev_onu + 1 if prev_onu is not None else 1
                        print(f"Onu kosong pada 1/{listed_uncfg[1]}/{listed_uncfg[2]}:{calculation}")
                        break
            
            elif "No related information to show" in output:
                calculation = 1
                print(f"Onu kosong pada 1/{listed_uncfg[1]}/{listed_uncfg[2]}:{calculation}")
                break

    except asyncio.exceptions.TimeoutError:
        pass
    
    writer.write("terminal length 200\n")
    await asyncio.sleep(0.3)

    return calculation

async def get_dba_profile_suffix(reader, writer, listed_uncfg):
    print("\nMengecek utilisasi bandwidth pada port OLT...")
    writer.write("terminal length 0\n")
    await asyncio.sleep(0.3)
    writer.write(f"show pon bandwidth dba interface gpon-olt_1/{listed_uncfg[1]}/{listed_uncfg[2]}\n")
    await asyncio.sleep(1)
    rate_percentage = 0.0
    THRESHOLD_RATE = 80.0
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
    writer.write("terminal length 200\n")
    await asyncio.sleep(0.3)
    return "MBW" if rate_percentage >= THRESHOLD_RATE else "FIX"

async def create_dba_profile(reader, writer, dba_profile_suffix, paket):
    print("Membuat DBA Profile...")
    writer.write("configure terminal\n")
    await asyncio.sleep(0.3)
    writer.write("gpon\n")
    await asyncio.sleep(0.3)
    paket_int = int(paket)
    if dba_profile_suffix == "MBW":
        if 1 <= paket_int <= 35:
            writer.write(f"profile tcont UP-{paket}MB-MBW type 1 assured 5000 maximum 30000\n")
            await asyncio.sleep(0.3)
        elif paket_int > 35:
            writer.write(f"profile tcont UP-{paket}MB-MBW type 5 fixed 15000 assured 10000 maximum {paket}000\n")
            await asyncio.sleep(0.3)
    else:
        if 1 <= paket_int <= 35:
            writer.write(f"profile tcont UP-{paket}MB-FIX type 1 fixed {paket}000\n")
            await asyncio.sleep(0.3)
        elif paket_int > 35:
            writer.write(f"profile tcont UP-{paket}MB-FIX type 1 fixed {paket}000\n")
            await asyncio.sleep(0.3)

    writer.write("exit\n")
    await asyncio.sleep(0.3)
    writer.write("exit\n")
    await asyncio.sleep(0.3)
    print(f"✅ DBA profile UP-{paket}MB-{dba_profile_suffix} telah berhasil dibuat.")

async def register_onu(reader, writer, listed_uncfg, calculation, jenismodem, nama_pelanggan, alamat, c600):
    print("PROSES KONFIGURASI ...")
    writer.write("configure terminal\n")
    await asyncio.sleep(0.3)
    if c600:
        writer.write(f"interface gpon_olt-1/{listed_uncfg[1]}/{listed_uncfg[2]}\n")
        await asyncio.sleep(0.3)
        writer.write(f"onu {calculation} type ALL sn {listed_uncfg[0]}\n")
        await asyncio.sleep(1.5)
        writer.write("exit\n")
        await asyncio.sleep(0.3)
        writer.write(f"interface gpon_onu-1/{listed_uncfg[1]}/{listed_uncfg[2]}:{calculation}\n")
        await asyncio.sleep(0.3)
    else:
        writer.write(f"interface gpon-olt_1/{listed_uncfg[1]}/{listed_uncfg[2]}\n")
        await asyncio.sleep(0.3)
        writer.write(f"onu {calculation} type ZTEG-F609 sn {listed_uncfg[0]}\n")
        await asyncio.sleep(1.5)
        writer.write("exit\n")
        await asyncio.sleep(0.3)
        writer.write(f"interface gpon-onu_1/{listed_uncfg[1]}/{listed_uncfg[2]}:{calculation}\n")
        await asyncio.sleep(0.3)

    writer.write(f"name {nama_pelanggan}\n")
    await asyncio.sleep(0.3)
    writer.write(f"description {alamat}\n")
    await asyncio.sleep(0.3)
    writer.write("exit\n")
    await asyncio.sleep(0.3)
    writer.write("exit\n") # Exit configure terminal
    await asyncio.sleep(0.3)

async def configure_onu_services(reader, writer, listed_uncfg, calculation, jenismodem, paket, pppoe, pass_ONT, vlan, c600, dba_profile_suffix, nama_pelanggan, alamat, olt_name):
    needs_profile_creation = False
    
    writer.write("configure terminal\n")
    await asyncio.sleep(0.3)
    
    if c600:
        writer.write(f"interface gpon_onu-1/{listed_uncfg[1]}/{listed_uncfg[2]}:{calculation}\n")
        await asyncio.sleep(0.3)
        writer.write(f"tcont 1 name PPPOE profile UP-{paket}MB-{dba_profile_suffix}\n")
        await asyncio.sleep(0.3)
        try:
            output = await asyncio.wait_for(reader.readline(), 1)
            if "Profile exceed" in output.lower() or "Profile does not exist" in output.lower():
                print("🚨 Utilisasi port penuh, reconfig dengan mode MBW")
                needs_profile_creation = True
        except asyncio.exceptions.TimeoutError:
            pass
        if not needs_profile_creation:
            writer.write("gemport 1 name CIGNAL tcont 1\n")
            await asyncio.sleep(0.3)
            writer.write("exit\n")
            await asyncio.sleep(0.3)
            writer.write(f"interface vport-1/{listed_uncfg[1]}/{listed_uncfg[2]}.{calculation}:1\n")
            await asyncio.sleep(0.3)
            writer.write(f"service-port 1 user-vlan {vlan} vlan {vlan}\n")
            await asyncio.sleep(0.3)
            writer.write(f"qos traffic-policy DOWN-{paket}M direction egress\n")
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
    
    #== C-DATA ==
    else:
        writer.write(f"interface gpon-onu_1/{listed_uncfg[1]}/{listed_uncfg[2]}:{calculation}\n")
        await asyncio.sleep(0.3)
        writer.write(f"tcont 1 name PPPOE profile UP-{paket}MB-{dba_profile_suffix}\n")
        await asyncio.sleep(0.3)
        try:
            output = await asyncio.wait_for(reader.readline(), 1)
            if "Profile exceed" in output.lower() or "Profile does not exist" in output.lower():
                print("🚨 Utilisasi port penuh, reconfig dengan mode MBW.")
                needs_profile_creation = True
        except asyncio.exceptions.TimeoutError:
            pass
        
        if not needs_profile_creation:
            writer.write("gemport 1 name PPPOE tcont 1\n")
            await asyncio.sleep(0.3)
            writer.write(f"gemport 1 traffic-limit downstream DOWN-{paket}M\n")
            await asyncio.sleep(0.3)
            
            if jenismodem == "ZTE":
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
            
            else:
                writer.write("encrypt 1 enable downstream\n")
                await asyncio.sleep(0.3)
                writer.write(f"service-port 1 vport 1 user-vlan {vlan} vlan {vlan}\n")
                await asyncio.sleep(0.3)
                writer.write("exit\n")
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
    
    if not needs_profile_creation:
        writer.write("int eth eth_0/1 sta lock\n")
        await asyncio.sleep(0.3)
        writer.write("int eth eth_0/2 sta lock\n")
        await asyncio.sleep(0.3)
        writer.write("int eth eth_0/3 sta lock\n")
        await asyncio.sleep(0.3)
        writer.write("int eth eth_0/4 sta lock\n")
        await asyncio.sleep(0.3)
        writer.write("exit\n")
        await asyncio.sleep(0.3)
        writer.write("exit\n")
        await asyncio.sleep(0.3)

    try:
        while True:
            output = await asyncio.wait_for(reader.readline(), 2)
            print(output.strip())
    except asyncio.exceptions.TimeoutError:
        pass
    
    if not needs_profile_creation:
        print("\nKONFIGURASI SELESAI")
        print(f"✅ Serial Number : {listed_uncfg[0]}")
        print(f"✅ ID pelanggan : {pppoe}")
        print(f"✅ Nama pelanggan : {nama_pelanggan}")
        print(f"✅ OLT dan ONU : {olt_name} 1/{listed_uncfg[1]}/{listed_uncfg[2]}:{calculation}")

    return needs_profile_creation


async def main():
    reader, writer = await connect_to_olt(ip, username, password)
    listed_uncfg = await find_uncfg_onu(reader, writer, c600)
    if listed_uncfg is None:
        writer.close()
        return

    print("1. F670L")
    print("2. C-DATA")
    while True:
        try:
            modem = int(input("🛜 Pilih Jenis Modem : "))
            if modem in [1, 2]:
                jenismodem = "ZTE" if modem == 1 else "C-DATA"
                break
            print("Maaf input tidak dimengerti")
        except ValueError:
            print("Input harus berupa angka.")

    calculation = await get_onu_placement(reader, writer, listed_uncfg, c600)
    dba_profile_suffix = await get_dba_profile_suffix(reader, writer, listed_uncfg)

    nama_pelanggan = input("👤 MASUKKAN NAMA PELANGGAN : ")
    alamat = input("📍 MASUKKAN ALAMAT PELANGGAN : ")
    pppoe = input("🌐 MASUKKAN NOMOR ID PELANGGAN : ")
    pass_ONT = input("🔒 MASUKKAN PASSWORD PPPOE : ")

    print("PILIH PAKET PELANGGAN:")
    print("1. 10M")
    print("2. 15M")
    print("3. 20M")
    print("4. 25M")
    print("5. 30M")
    print("6. 35M")
    print("7. 40M")
    print("8. 45M")
    print("9. 50M+")
    while True:
        try:
            cek = int(input("PILIH PAKET PELANGGAN : "))
            paket_map = {1: "10", 2: "15", 3: "20", 4: "25", 5: "30", 6: "35", 7: "40", 8: "45", 9: "100"}
            paket = paket_map.get(cek)
            if paket:
                break
            else:
                print("Paket internet tidak ditemukan. Silakan pilih nomor dari 1-9.")
        except ValueError:
            print("Input tidak valid. Silakan masukkan angka.")
    
    await register_onu(reader, writer, listed_uncfg, calculation, jenismodem, nama_pelanggan, alamat, c600)

    needs_profile_creation = await configure_onu_services(reader, writer, listed_uncfg, calculation, jenismodem, paket, pppoe, pass_ONT, vlan, c600, dba_profile_suffix, nama_pelanggan, alamat, olt_name)
    
    if needs_profile_creation:
        await create_dba_profile(reader, writer, dba_profile_suffix, paket)
        print("\nRetrying service configuration with the new DBA profile...")
        await configure_onu_services(reader, writer, listed_uncfg, calculation, jenismodem, paket, pppoe, pass_ONT, vlan, c600, dba_profile_suffix, nama_pelanggan, alamat, olt_name)
    
    writer.write("exit\n")
    await asyncio.sleep(0.5)
    writer.close()

if __name__ == '__main__':
    asyncio.run(main())
