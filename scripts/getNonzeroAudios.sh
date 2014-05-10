#!/bin/bash

for f in $1/*
do
    command="soxi -d $f"
    len=`$command 2>&1`;
    echo "LEN: $len";
    if [[ $len != soxi* ]] 
    #if [[ soxi == s* ]] 
    then
	command="cp $f $2";
	echo $command
	eval $command

    fi
done