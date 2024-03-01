# import requests
# import ssl
# import whois
# from datetime import datetime, timezone
# import tzlocal
# from ping3 import ping, verbose_ping
# time_zone = tzlocal.get_localzone()
# now = datetime.now(time_zone)
# format_str = "%Y-%m-%d %H:%M:%S"

# def collect_data(url):
#    data = {}
#    try:
#       with requests.get(url, stream=True) as response:
#          data['request_datetime'] = datetime.now(time_zone).strftime(format_str)
#          data['domain'] = url[8:]
#          data['ping'] = round(ping(data['domain'], unit='ms'))
#          data['respones_time'] = round(response.elapsed.total_seconds() * 1000)
#          w = whois.whois(data['domain'])

#          certificate_info_raw = response.raw.connection.sock.getpeercert(True)
#          certificate_info = response.raw.connection.sock.getpeercert()

#          data['cert'] = ssl.DER_cert_to_PEM_cert(certificate_info_raw)
#          data['status_code'] = response.status_code

#          tmp =  datetime.strptime((certificate_info["notBefore"])[0:-4], '%b %d %H:%M:%S %Y')
#          data['cert_from'] = tmp.replace(tzinfo=timezone.utc).astimezone(time_zone).strftime(format_str)

#          tmp =  datetime.strptime((certificate_info["notAfter"])[0:-4], '%b %d %H:%M:%S %Y')
#          data['cert_to'] = tmp.replace(tzinfo=timezone.utc).astimezone(time_zone).strftime(format_str)

#          if type(w.expiration_date) == list:
#             w.expiration_date = w.expiration_date[0]

#          data['domain_exp'] = w.expiration_date.replace(tzinfo=timezone.utc).astimezone(time_zone).strftime(format_str)

#          timedelta = w.expiration_date - now
#          data['days_to_domain_exp'] = timedelta.days

#          match data['status_code']:
#             case code if code >=100 and code <= 199:
#                data['status'] = "Informational responses"
#             case code if code >=200 and code <= 299:
#                data['status'] = "Successful responses"
#             case code if code >=300 and code <= 399:
#                data['status'] = "Redirection messages"
#             case code if code >=400 and code <= 499:
#                data['status'] = "Client error responses"
#             case code if code >=500 and code <= 599:
#                data['status'] = "Server error responses "

#          return data
      
#    except Exception as e:
#       print(e)


# def ssl_monitor(url, timeout, monitor_id, days_before_to_inform):
#    data = {}
#    try:
#       with requests.get(url, stream=True, timeout=timeout) as response:
#          data['domain'] = url[8:]
#          w = whois.whois(data['domain'])
#          certificate_info = response.raw.connection.sock.getpeercert()
#          tmp =  datetime.strptime((certificate_info["notBefore"])[0:-4], '%b %d %H:%M:%S %Y')
#          data['cert_from'] = tmp.replace(tzinfo=timezone.utc).astimezone(time_zone).strftime(format_str)

#          tmp =  datetime.strptime((certificate_info["notAfter"])[0:-4], '%b %d %H:%M:%S %Y')
#          data['cert_to'] = tmp.replace(tzinfo=timezone.utc).astimezone(time_zone).strftime(format_str)

#          if type(w.expiration_date) == list:
#             w.expiration_date = w.expiration_date[0]

#          data['domain_exp'] = w.expiration_date.replace(tzinfo=timezone.utc).astimezone(time_zone).strftime(format_str)

#          timedelta = w.expiration_date.replace(tzinfo=timezone.utc).astimezone(time_zone) - now
#          data['days_to_domain_exp'] = timedelta.days

#          timedelta = (tmp.replace(tzinfo=timezone.utc).astimezone(time_zone)) - now
#          data['days_to_ssl_exp'] = timedelta.days

#          if(data['days_to_ssl_exp'] < days_before_to_inform):
#             for tmp in EmailValues.objects.filter(monitor_id=monitor_id):
#                send_mail(
#                   f"Twój certyfikat SSL wygasa za {data['days_to_ssl_exp']}",
#                   f"Ważność twojego certyfikatu SSL dobiega końca, natomiast domena wygasa: {data['days_to_domain_exp']}",
#                   settings.EMAIL_HOST_USER,
#                   [tmp.email],
#                   fail_silently=False,
#                )


#    except Exception as e:
#       print(e)

# ssl_monitor("https://google.com",5,2,10000)