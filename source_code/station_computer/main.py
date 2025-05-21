########################################################################################################################
#                                                                                                                      #
#    Author:         D. Nenicka                                                                                        #
#    Created:        3. 11. 2023                                                                                       #
#    Modified:       19. 10. 2024                                                                                      #
#    Description:    The main script of Satellite Tracking Software                                                    #
#                                                                                                                      #
########################################################################################################################


from TrackingTool import TrackingTool                               # Satellite Tracking Software GUI


if __name__ == '__main__':
    app = TrackingTool('configuration.json')
    app.mainloop()
