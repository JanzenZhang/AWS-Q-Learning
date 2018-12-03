
# README

## Fuzzy-Q-Learning

A source code implementation of Fuzzy Q-Learning in OpenStack (IaaS cloud infrastructure)
It divide into main part : 1) HEAT template files for creating your own stack in OpenStack and 2) source code implementation of FQL in Python which will be run and executed inside of control VM created by HEAT files

### Create your stack :

```
heat stack-create -f autoscaling.yaml \
-P network=$(neutron net-show private -F id -f value) \
-P subnet_id=$(neutron subnet-show private-subnet -F id -f value) \
-P external_network_id=$(neutron net-show public -F id -f value) \
-P OS_AUTH_URL=$OS_AUTH_URL \
-P desired_capacity=1 \
asg
```


### Verify Stack creation:
```
heat stack-list ; nova list
```

also, you can modify any input parameters in HEAT template file (autoscaling.yaml) by passing your prefered value in 'heat stack-create' command

# Contact

If you notice a bug, want to request a feature, or have a question or feedback, please send an email to hamid.arabnejad@gmail.com

