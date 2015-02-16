import sys
from subprocess import Popen, PIPE
import operator
import json
from time import gmtime, strftime
import hashlib




def is_json(test_json):
    try:
        json_object = json.loads(test_json)
    except ValueError, e:
        print str(e)
        return False
    return True



def get_pip_packages():

    try:

        import pip
        print("Getting Packages...")
        installed_packages = pip.get_installed_distributions()
        installed_packages_list = sorted(["%s==%s" % (i.key, i.version)
                                           for i in installed_packages])

        return installed_packages_list
    except:
        print ("Issue with PIP")
        return []

try:
    elasticsearch_url = sys.argv[1]
except:
    elasticsearch_url = None

# prepare dict to load into ElasticSearch
master_dict = {}

#add gmt time
master_dict['date_created'] = strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())

#get host name
p = Popen("hostname ", shell=True, stdout=PIPE)
host_name = p.stdout.read().splitlines()[0]
print host_name
master_dict['host_name'] = host_name

#get the machine ip address
p = Popen("/sbin/ifconfig eth0 | awk '/inet/ { print $2 } ' | sed -e s/addr://", shell=True, stdout=PIPE)
ip_address = p.stdout.read().splitlines()[0]
master_dict['ip_address'] = ip_address


#create a unique id for this json
_id = strftime("%a%b%Y%H:%M:%S", gmtime()) + host_name
_id = hashlib.sha224(_id).hexdigest()


#call each virtualenv and figure out what python libaries are installed
p = Popen("source $(which virtualenvwrapper.sh) && lsvirtualenv -b  ", shell=True, stdout=PIPE)

_list = p.stdout.read().splitlines()
print "list here", _list

json_pattern = '"$virtualenvName" : $list '

virtualenvs_json_list = []


for virtualenv in _list:
    print("Virtualenv: " + virtualenv)
    cmd = "source $(which virtualenvwrapper.sh) ; workon " + virtualenv + " ; pip freeze"
    p = Popen(cmd, shell=True, stdout=PIPE)
    temp_list = p.stdout.read().splitlines()
    temp_list.append(get_pip_packages())
    current_virtualenv = {}
    current_virtualenv[virtualenv] = temp_list

    virtualenvs_json_list.append(current_virtualenv)

# if virtualenvs_json_list:
master_dict['python_libraries'] = virtualenvs_json_list
    # master_json = master_json.replace("$python_libraries", python_installed + "," +  ",".join(virtualenvs_json_list) )
# else:
#     master_dict['']
#     master_json = master_json.replace("$python_libraries", python_installed  )

# Scrape ruby packages
p = Popen('find / -type f -name "gem" 2>/dev/null', shell=True, stdout=PIPE)

output = p.stdout.read().splitlines()

envs = {}
for line in output:
    p = Popen('%s list | grep -v "*** LOCAL"' % line, shell=True, stdout=PIPE)
    gems = p.stdout.read().splitlines()
    gems_clean = []
    envs[line] = gems

# json_envs = json.dumps(envs)

master_dict['ruby_libraries'] = envs

#view all the processes that are currently running
cmd = "ps -e -o comm --sort=-comm"
p = Popen(cmd, shell=True, stdout=PIPE)

dict_proc = {}

#do this to remove duplicates
for i in p.stdout.read().splitlines():
    dict_proc[i] = i

sorted_dict_proc = sorted(dict_proc.items(), key=operator.itemgetter(0))

json_temp = [item[0] for item in sorted_dict_proc]

master_dict['processes'] = json_temp


# Call yum and scrub out all that crazy amount of white space.
p = Popen("sudo yum list installed", shell=True, stdout=PIPE)

temp_yum = p.stdout.read().splitlines()

json_temp = json.dumps(temp_yum)
json_temp = json_temp.replace("               ","  ")
json_temp = json_temp.replace("            ","  ")
json_temp = json_temp.replace("         ","  ")
json_temp = json_temp.replace("        ","  ")
json_temp = json_temp.replace("      ","  ")
json_temp = json_temp.replace("     ","  ")

master_dict['yum_installed'] = json_temp




#get iptables
p = Popen("sudo iptables -L -v -n", shell=True, stdout=PIPE)

temp_iptables = p.stdout.read().splitlines()
# print temp_iptables
json_temp = json.dumps(temp_iptables)
json_temp = json_temp.replace("'","")
master_dict['iptables'] = json.loads(json_temp)

#post to elasticsearch

# if elasticsearch_url != None:
run_curl = "curl -XPUT %s/installedsoftware/%s/%s -d ' %s '" % (elasticsearch_url,host_name , _id, json.dumps(master_dict))
print run_curl

    # p = Popen(run_curl, shell=True, stdout=PIPE)
    # print p.stdout.read()
# else:
#     # print master_dict
#     pass


with open('blahcrap2.txt', 'w') as f:
    f.write(json.dumps(master_dict))