
macroman
========

There are many HTML5 build tools out there.
But probally none that supports all templating engines you want to use.
In macroman to add for example support for CoffeeScript you need nothing more than the following line in your config.macroman.

	:: coffee -c {file}

And this is how we tell macroman to "compile" all .coffee files to .js with CoffeeScript

	*.coffee -> coffee => *.js

You can fine-tune the compilation process:

	simpleStylus :: stylus {file}
	
	myOtherStylus :: stylus --out {tmpdir} --use /usr/local/lib/node_modules/nib/lib/nib.js {file}
	myOtherStylus.copy :: no
	myOtherStylus.outfile :: {tmpdir}/{filebase}.css

Another example:

	bcoffee ::  coffee --contracts --bare --compile {file}
	commonjs :: {bin}/to_commonjs.py {file}
	
	*.coffee -> bcoffee -> commonjs => *.js


Files are compiled on the fly by the development server.

Please note that I did macroman as a tool for another personal project and it still needs work before you can use it without expaning the code.









