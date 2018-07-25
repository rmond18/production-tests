#!/bin/bash

source $SCRIPT_DIR/config.sh
source $SCRIPT_DIR/lib/preflash.sh
source $SCRIPT_DIR/lib/flash.sh

#----------------------------------#
# Functions section                #
#----------------------------------#

show_leds() {
	local leds

	if [ "$PASSED" == "1" ] ; then
		leds="$leds $PASSED_LED"
	fi

	if [ "$READY" == "1" ] ; then
		leds="$leds $READY_LED"
	fi

	if [ "$FAILED" == "1" ] ; then
		leds="$leds $FAILED_LED"
	fi

	if [ "$PROGRESS" == "1" ] ; then
		leds="$leds $PROGRESS_LED"
	fi

	toggle_pins D $leds
}

show_ready_state() {
	PROGRESS=0
	READY=1
	show_leds
}

show_start_state() {
	PASSED=0
	READY=0
	FAILED=0
	PROGRESS=1
	show_leds
}

show_error_state() {
	FAILED=1
	show_leds
}

need_to_read_eeprom() {
	[ "$FAILED" == "1" ] || [ -z "$VREF" ] || [ -z "$VOFF" ] || [ -z "$VGAIN" ]
}

inc_fail_stats() {
	local serial="$1"
	let FAILED='FAILED + 1'
	echo "PASSED=$PASSED" > $STATSFILE
	echo "FAILED=$FAILED" >> $STATSFILE
	[ -z "$serial" ] || echo "FAILED $serial" >> $RESULTSFILE
}

inc_pass_stats() {
	local serial="$1"
	let PASSED='PASSED + 1'
	echo "PASSED=$PASSED" > $STATSFILE
	echo "FAILED=$FAILED" >> $STATSFILE
	[ -z "$serial" ] || echo "PASSED $serial" >> $RESULTSFILE
}

#----------------------------------#
# Main section                     #
#----------------------------------#

production() {
	local TARGET="$1"
	local PASSED FAILED

	[ -n "$TARGET" ] || {
		echo_red "No target specified"
        	return 1
	}
	[ -f "$SCRIPT_DIR/config/$TARGET/postflash.sh" ] || {
		echo_red "File '$SCRIPT_DIR/config/$TARGET/postflash.sh' not found"
		return 1
	}

	source $SCRIPT_DIR/config/$TARGET/postflash.sh

	# State variables; are set during state transitions
	local PASSED=0
	local FAILED=0
	local READY=0
	local PROGRESS=0

	local EEPROM_VERBOSE=1

	# This will store in a `log` directory the following files:
	# * _results.log - each device that has passed or failed with S/N
	#    they will only show up here if they got a S/N, so this assumes
	#    that flashing worked
	# * _errors.log - all errors that don't yet have a S/N
	# * _stats.log - number of PASSED & FAILED
	local LOGDIR=$SCRIPT_DIR/log
	local LOGFILE=$LOGDIR/temp.log # temp log to store stuff, before we know the S/N of device
	local ERRORSFILE=$LOGDIR/_errors.log # errors that cannot be mapped to any device (because no S/N)
	local STATSFILE=$LOGDIR/_stats.log # stats ; how many passes/fails
	local RESULTSFILE=$LOGDIR/_results.log # format is "<BOARD S/N> = OK/FAILED"

	# Remove temp log file start (if it exists)
	rm -f "$LOGFILE"

	echo_green "Initializing FTDI pins to default state"
	init_pins

	# send STDERR to STDOUT
	exec 2>&1

	# file descriptor 4 prints to STDOUT and to LOGFILE
	exec 4> >(while read a; do echo $a; echo $a >>$LOGFILE; done)

	while true ; do

		if need_to_read_eeprom ; then
			echo_green "Loading settings from EEPROM"
			eeprom_cfg load || {
				echo_red "Failed to load settings from EEPROM..."
				sleep 3
				continue
			}
		fi

		show_ready_state || {
			echo_red "Cannot enter READY state"
			sleep 3
			continue
		}

		echo_green "Waiting for start button"

		wait_pins D "$START_BUTTON" || {
			echo_red "Waiting for start button failed..."
			show_error_state
			sleep 3
			continue
		}

		show_start_state

		mkdir -p $LOGDIR

		if [ -f "$STATSFILE" ] ; then
			source $STATSFILE
		fi
		[ -n "$PASSED" ] || PASSED=0
		[ -n "$FAILED" ] || FAILED=0

		if [ -f "$LOGFILE" ] ; then
			cat "$LOGFILE" >> "$ERRORSFILE"
			rm -f "$LOGFILE"
		fi

		exec >&4

		pre_flash "$TARGET" || {
			echo_red "Pre-flash step failed..."
			show_error_state
			inc_fail_stats
			sleep 3
			continue
		}

		retry 4 flash "$TARGET" || {
			echo_red "Flash step failed..."
			show_error_state
			inc_fail_stats
			sleep 3
			continue
		}

		local serial
		for _ in $(seq 1 20) ; do
			serial=$(get_hwserial)
			[ -z "$serial" ] || break
			sleep 1
		done
		[ -n "$serial" ] || {
			echo_red "Could not get device serial number"
			show_error_state
			sleep 3
			continue
		}

		post_flash "dont_power_cycle_on_start" || {
			echo_red "Post-flash step failed..."
			show_error_state
			mv -f $LOGFILE "$LOGDIR/${serial}.log"
			inc_fail_stats "$serial"
			sleep 3
			continue
		}
		mv -f $LOGFILE "$LOGDIR/${serial}.log"
		inc_pass_stats "$serial"
		PASSED=1
	done
}