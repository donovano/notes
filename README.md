Notes
=====
A python based web app that can easily be hosted on your private network e.g. at home like on a Raspberry Pi or on a cloud service provider etc

### Demo
[https://rl8td.com](https://rl8td.com)

### Instructions
All the components to host it are free and open source except if you would like to use your own domain and don’t have one yet. Hosting it without a domain is possible but since you’d want to host it over an encrypted connection (https) you’d need a certificate which is problematic (but can be overcome) without your own domain.

One way to host Notes is to use nginx and uwsgi. Nginx is the web server and uwsgi provides it the capability to communicate with the python Flask Notes app. See this article for a good overview of the topic: http://www.ines-panker.com/2020/02/16/nginx-uwsqi.html

You will also need to install mongodb which is the database used to store the notes.

As mentioned, preferably you will use our own domain name, which is cheap and easy to obtain from a provider like Godaddy. You can then get a certificate for this from Letsencrypt which automates the process of configuring your nginx server with the needed cryptographic configuration.

