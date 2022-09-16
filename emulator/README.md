## Emulator

We resort to p4lang [BMv2 tools](https://github.com/p4lang/tutorials) to perform evaluation.  

### Quick Start 

1. Install BMv2 according to the documentation
  1. Please follow the installation using the vagrant, the virtual machine
  2. The docker source might be unavailable in some specific areas.
  3. You might have to mount the modified example to the location of `/home/p4/git/tutorial/exercise` within the vm

2. Make and run
  1. After successfully executing the [example](https://github.com/p4lang/tutorials/tree/master/exercises/basic), change directory to the `/exercise` directory
  2. First run `make run` as well
  3. Run `h1 python2 send.py -e 3`
  4. Leave the mininet environment using "ctrl+C"
  5. The link usage conditon will then show in the `\analysis`directory


P.S. If you failed to perform the steps above,
  1. First, you should at least be able to run exercises within [BMv2](https://github.com/p4lang/tutorials).
  2. Then, you can view the two seperate directories in `/example` in our repo as additional exercises in BMv2, 
  then import these two into the exercises in BMv2.
  3. Then, continue perform make and run.