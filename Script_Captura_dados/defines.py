# Arquivo responsavel por guardar DEFINES e caminho absoluto para leitura dos arquivos

# Caminho completo para os arquivos do Dessem
CAMINHO = '/home/francisco/Documents/TCC2/Projeto/Ferramenta-de-conversao/'

# Pasta com arquivos Dessem obtido ONS
BLOCO_REVISAO = 'ds_ons_122023_rv0d29'

# Arquivos para coleta do caso base, antes da mudança de patamar
LEVE_PWF = CAMINHO+BLOCO_REVISAO+'/leve.pwf'
MEDIA_PWF = CAMINHO+BLOCO_REVISAO+'/media.pwf'
PESADA_PWF = CAMINHO+BLOCO_REVISAO+'/pesada.pwf'

########## Arquivos de Usinas #############
USINA_HIDRAULICA = CAMINHO+BLOCO_REVISAO+'/pdo_hidr.dat'
USINA_TERMOELETRICA = CAMINHO+BLOCO_REVISAO+'/pdo_term.dat'


# Arquivo responsavel por informar o arquivo de caso base de acordo com o estagio requirido
DESSELET_DAT = CAMINHO+BLOCO_REVISAO+'/desselet.dat'

DIRETORIO_COM_RESULTADOS_DE_SAIDA = CAMINHO+'Resultados_Ferramenta_Computacional_'+BLOCO_REVISAO+'/'
