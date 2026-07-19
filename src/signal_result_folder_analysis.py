from analiz import ortalama, maximum, square

def read_file(file_path):
    """
    Reads the content of a file and returns it as a string.

    Args:
        file_path (str): The path to the file to be read.

    Returns:
        str: The content of the file.
    """
    with open(file_path, 'r') as file:
        return file.read()
    
def write_file(file_path, content):
    """
    Writes the given content to a file.

    Args:
        file_path (str): The path to the file where the content will be written.
        content (str): The content to be written to the file.
    """
    with open(file_path, 'w') as file:
        file.write(content)

def main():
    file_path = 'olcumler.txt'
    content = read_file(file_path)

    split_content = content.splitlines()
    dict_content = {}
    for line in split_content:
        kanal, deger = line.split(',')
        deger = float(deger)  # Convert the value to float
        dict_content.setdefault(kanal, []).append(deger)

    print("File Content:")
    print(content)
    print("\nSplit Content:")
    for line in split_content:
        print(line)
    print("\nDictionary Content:")
    for key, value in dict_content.items():
        print(f"{key}: {value}")

    for kanal, degerler in dict_content.items():
        print(f"Kanal: {kanal} : Ortalama: {ortalama(degerler)}, Maximum: {maximum(degerler)}")

    print("ch1 Değerler ve Kareleri:")
    print(f"Değerler: {dict_content['ch1']} : Kareleri: {square(dict_content['ch1'])}")
    buyuk_degerler = [deger for degerler in dict_content.values() for deger in degerler if deger > 3.0]
    print(f"3.0'dan büyük değerler: {buyuk_degerler}")

    print(f"kanallar; {', '.join(dict_content.keys())}")

    print("ch1 listesinin ilk 2 elemanını, son elemanını ve tersten hali")
    ch1_list = dict_content.get('ch1', [])
    print(f"İlk 2 eleman: {ch1_list[:2]}")
    print(f"Son eleman: {ch1_list[-1]}")
    print(f"Tersten hali: {ch1_list[::-1]}")

    lines = []
    for kanal, degerler in dict_content.items():
        lines.append(f"{kanal}: ortalama={ortalama(degerler):.2f}, max={maximum(degerler)}")
    
    write_file('sonuclar.txt', "\n".join(lines))


if __name__ == "__main__":
    main()
    