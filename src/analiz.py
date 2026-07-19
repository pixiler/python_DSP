def even_count(sayilar):
    count = 0
    for sayi in sayilar:
        if sayi % 2 == 0:
            count += 1
    return count

def maximum(sayilar):
    if not sayilar:
        return None
    max_sayi = sayilar[0]
    for sayi in sayilar:
        if sayi > max_sayi:
            max_sayi = sayi
    return max_sayi

def ortalama(sayilar):
    toplam = 0
    count = 0
    for sayi in sayilar:
        toplam += sayi
        count += 1
    return toplam/count if count > 0 else 0

def square(sayilar):
    return [sayi ** 2 for sayi in sayilar]

def analiz(sayilar):
    ortalama_sayi = ortalama(sayilar)
    maximum_sayi = maximum(sayilar)
    cift_sayi_count = even_count(sayilar)
    return ortalama_sayi, maximum_sayi, cift_sayi_count

def main():
    sayilar = [3, 8, 1, 12, 7, 6]
    ortalama, max_sayi, cift_sayi_count = analiz(sayilar)
    print(f"Ortalama: {ortalama}")
    print(f"Maximum Sayı: {max_sayi}")
    print(f"Çift Sayılar: {cift_sayi_count}")

if __name__ == "__main__":
    main()