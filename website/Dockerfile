# Use a imagem do nginx para servir arquivos estáticos
FROM nginx:alpine

# Copia todos os arquivos do website para o diretório padrão do nginx
COPY . /usr/share/nginx/html

# Copia a configuração customizada do nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expõe a porta 80
EXPOSE 80

# O nginx roda automaticamente quando o container inicia
CMD ["nginx", "-g", "daemon off;"]
