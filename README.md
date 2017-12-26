# XL Release Fastlane plugin v1.0.0

## Preface ##

This document describes the functionality provided by the XL Release fastlane plugin.  fastlane is an open source platform aimed at simplifying Android and iOS deployment.  The plugin gives you the ability to checkout a repo and invoke a fastlane 'lane' on a remote server.

See the **[XL Release Documentation](https://docs.xebialabs.com/xl-release/)** for background information on XL Release concepts.

## Overview ##

The XL Release Fastlane plugin enables you interact with BMC Fastlane services.  The plugin supports the following tasks:

#### Task : Lane Task ####

__ Parameters __

Name | Description
------ | -------
Client Host | Fastlane host defined in Settings > Shared Configuration
Git Project URL | GIT repository to checkout (optional).  If blank, the target directory is used "as is" without a code checkout. 
Branch | GIT branch used
Working Dir | Directory on the remote server to run fastlane.
Lane | The fastlane lane to invoke.
Options | Map of options passed to fastlane

## Requirements ##
* **XL Release** 7.x
* ssh running on the target computer

## Installation ##

* Place the plugin JAR file into your `SERVER_HOME/plugins` directory.
* Restart the server  
