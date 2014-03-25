import re, configparser

def getPassword():
    global nscparser, final_token
    dictSettings = dict(nscparser.items("Settings"))
    final_token = dictSettings["password"]

def getPluginDirectives():
    global nscparser, final_plugins
    dictPluginDirectives = dict(nscparser.items("Script Wrappings"))
    plugins = ""
    for key in dictPluginDirectives:
        plugins += ".%s=%s\n" % (key, dictPluginDirectives[key])
    plugins = plugins.replace("%SCRIPT%", "$plugin_name")
    plugins = plugins.replace("%ARGS%", "$plugin_args")
    final_plugins = plugins.strip()

def getPassiveChecks():
    global nscparser, final_passive
    dictPassiveChecks = dict(nscparser.items("NSCA Commands"))
    
    passive = ""
    half_passive = ""
    ncpa_passive1 = "%%HOSTNAME%%|%s =%s --warning %s"
    ncpa_passive2 = " --critical %s\n"
    final_passive = ""
    specific_stat = ""
    defaults = ["cpu", "disk", "mem", "memory"]
    check_check = False
    test_check = False
    
    for key in dictPassiveChecks:
        passive += "%s=%s \n" % (key, dictPassiveChecks[key])
    passive = re.split("[= ]", passive)    

    for i, value in enumerate(passive):
        if "cpu" in value.lower():
            if "count" in value.lower():
                specific_stat = "/count"
            elif "idle" in value.lower():
                specific_stat = "/idle"
            elif "system" in value.lower():
                specific_stat = "/system"
            elif "user" in value.lower():
                specific_stat = "/user"
            else:
                specific_stat = "/percent"
            if "warn" in passive[i+2].lower():
                half_passive = ncpa_passive1 % ("CPU Usage", 
                " /cpu%s" % specific_stat, passive[i+3].replace("%", ""))
                half_passive = half_passive.strip()
            if "crit" in passive[i+4].lower():
                half_passive += ncpa_passive2 % (passive[i+5].replace("%", ""))
                final_passive += half_passive
            
        elif "disk" in value.lower():
            if "logical" in value.lower():
                specific_stat = "/logical"
            elif "physical" in value.lower():
                specific_stat = "/physical"
            else:
                specific_stat = ""
            if "warn" in passive[i+2].lower():
                half_passive = ncpa_passive1 % ("Disk Usage", 
                " /disk%s" % specific_stat, passive[i+3].replace("%", ""))
                half_passive = half_passive.strip()
            if "crit" in passive[i+4].lower():
                half_passive += ncpa_passive2 % (passive[i+5].replace("%", ""))
                final_passive += half_passive
                
        elif "mem" in value.lower() or "memory" in value.lower():
            if "swap" in value.lower():
                specific_stat = "/swap"
            elif "virtual" in value.lower():
                specific_stat = "/virtual"
            else:
                specific_stat = ""
            if "warn" in passive[i+2].lower():
                half_passive = ncpa_passive1 % ("Memory Usage", 
                " /memory%s" % specific_stat, passive[i+3].replace("%", ""))
                half_passive = half_passive.strip()
            if "crit" in passive[i+4].lower():
                half_passive += ncpa_passive2 % (passive[i+5].replace("%", ""))
                final_passive += half_passive
##        if "check" in value:
##            for val in defaults:
##                if val in value:
##                    check_check = True
##                else:
##                    check_check = False
##                    if "check" in passive[i+1]:
##                        test_check = True
##                    else:
##                        test_check = False
##                if check_check == True:
##                        for x, val in enumerate(passive):
##                            print x
##                    half_passive = ncpa_passive1 % (value, passive, value)
            

def main():
    global nscparser, final_token, final_plugins, final_passive
    nscparser = configparser.ConfigParser()
    nscparser.read("NSC.ini")
    
    getPassword()
    getPluginDirectives()
    getPassiveChecks()
    
    print("Some stuff:")
    print((final_token + "\n"))
    print((final_plugins + "\n"))
    print((final_passive + "\n"))
main()






# Builds NCPA configuration file 
s = open("ncpa_template.txt").read()
s = s.replace("{token}", final_token)
s = s.replace("{plugins}", final_plugins)
s = s.replace("{checks}", final_passive)
ncpa = open("ncpa.cfg", "w")
ncpa.write(s)
ncpa.close()






