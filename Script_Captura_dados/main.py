from mod_arquivos import tratamentoGeralArquivos

if __name__ == "__main__":

    print('Horario entre 00:00 e 23:30')
    hora = str(input('Informe a hora, respeitando as seguintes entradas: 00, 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23\nHora desejada: '))
    minutos = str(input('Informe os minutos, respeitando as seguintes entradas: 00, 30\nMinuto desejado: '))
    
    objetoContendoInformacoesGerais = tratamentoGeralArquivos(hora, minutos)