#CÓDIGO BASEADO NO EXERCICIO 5 DA LISTA A

cp=1004 #calor a pressao costante
cv=717 #calor a volume constante
k=1.4 #razão cos calores

def receber_inputs():
    P1=float(input("P1(Kpa): "))# pressão admissão
    P1=P1*10**3 #conversão para Pa
    T1=float(input("T1(K): "))#Temperatura de admissão
    RP=float(input("RP: ")) #Relação de pressões 
    W=float(input("W(MW): ")) #Potência Líquida 
    W=W*10**6 #Conversão para W
    T4=float(input("Tmax(K): ")) #Temperatura saída camara de combustão
    return P1, T1, RP, W, T4
p1, T1, RP, W, T4 = receber_inputs()
    
def calculo_ciclo_brayton(P1, T1, RP, W, T4):
    def calculo_compressao(P1,T1,RP,cp, k):
        P2=RP*P1 #Calulo de P2 com base em P1 e Rp
        T2=T1*(RP)**((k-1)/k) #Relação isentrópica entre temperatura e pressão para calcular T2
        Wc=cp*(T2-T1) #Trabalho do compressor KJ/Kg
        return P2, T2, Wc
    P2,T2,Wc = calculo_compressao(P1, T1, RP, cp, k)

    def calculo_turbina(T4,P1, P2, cp, k):
        P4=P2
        P3=P2 
        P5=P1
        P6=P1
        T5=T4*(P5/P4)**((k-1)/k)#Temperatura saida da turbina
        Wt=cp*(T4-T5) #Trabalho da turbina KJ/Kg
        return T5, Wt
    T5, Wt = calculo_turbina(T4, P1, P2, cp, k)

    def calculo_constantes(Wc, Wt):
        Wliq = Wt - Wc #Trabalho Liquido do ciclo 
        vazaom= W/Wliq #Vazão Mássica
        eficiencia=Wliq/Wt #Eficiência do Ciclo
        return Wliq, vazaom, eficiencia
    Wliq, vazaom, eficiencia = calculo_constantes(Wc, Wt)
    return P2, T2, Wc, T5, Wt, Wliq, vazaom, eficiencia
P2, T2, Wc, T5, Wt, Wliq, vazaom, eficiencia = calculo_ciclo_brayton(p1, T1, RP, W, T4)

#EXIBIR RESULTADOS
print("\n")
print(f"P2: {P2 / 1_000:.2f} kPa")
print(f"T2: {T2:.2f} K")
print(f"Wc: {Wc / 1_000:.2f} kJ/kg")
print(f"T5: {T5:.2f} K")
print(f"Wt: {Wt / 1_000:.2f} kJ/kg")
print(f"Wliq: {Wliq / 1_000:.2f} kJ/kg")
print(f"m: {vazaom:.2f} kg/s")
print(f"ef: {eficiencia * 100:.2f} %")

