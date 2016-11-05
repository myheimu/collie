#!/bin/bash

echo 'delete collie.zip if existed'
rm ../collie.zip
echo 'zip collie project into collie.zip [located on parent folder]'
zip -r ../collie.zip * -x *.git* *.pyc *migrations/0*
